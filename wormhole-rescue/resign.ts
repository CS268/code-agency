import 'dotenv/config';
import axios from 'axios';
import { eth } from 'web3';
import { deserialize, serialize, VAA, Signature } from '@wormhole-foundation/sdk';
import { RPC, ETH_CORE, WORMHOLESCAN_API, VAA_ID, PARSE_AND_VERIFY_VM_ABI } from './constants.js';
import { PARSE_AND_VERIFY_VM_ABI as LAYOUT } from './layouts.js';

async function fetchVaa(vaaId: string): Promise<string | null> {
  console.log('Fetching VAA for ID:', vaaId);
  try {
    const response = await axios.get(`${WORMHOLESCAN_API}/signed_vaa/${vaaId}`);
    const vaaBytes = response.data.vaaBytes;
    console.log('✅ VAA found!');
    return vaaBytes;
  } catch (error: any) {
    console.error('❌ Error fetching VAA:', error.message);
    return null;
  }
}

async function checkVaaValidity(vaaBytes: string) {
  console.log('\nChecking VAA validity...');
  try {
    const vaa = Buffer.from(vaaBytes, 'base64');
    vaa[4] = 4;
    
    const result = await axios.post(RPC, {
      jsonrpc: '2.0',
      id: 1,
      method: 'eth_call',
      params: [
        {
          from: null,
          to: ETH_CORE,
          data: eth.abi.encodeFunctionCall(LAYOUT, [`0x${vaa.toString('hex')}`]),
        },
        'latest',
      ],
    });
    
    const decoded = eth.abi.decodeParameters(LAYOUT.outputs, result.data.result);
    console.log(`${decoded.valid ? '✅' : '❌'} VAA Valid: ${decoded.valid}${decoded.valid ? '' : `, Reason: ${decoded.reason}`}`);
    return { valid: decoded.valid, reason: decoded.reason };
  } catch (error: any) {
    console.error('❌ Error checking VAA validity:', error.message);
    return { valid: false, reason: 'RPC error' };
  }
}

async function fetchObservations(vaaId: string) {
  console.log('\nFetching observations...');
  try {
    const response = await axios.get(`https://api.wormholescan.io/api/v1/observations/${vaaId}`);
    return response.data.map((obs: any) => ({
      guardianAddr: obs.guardianAddr.toLowerCase(),
      signature: obs.signature,
    }));
  } catch (error: any) {
    console.error('❌ Error fetching observations:', error.message);
    return [];
  }
}

async function fetchGuardianSet() {
  console.log('\nFetching current guardian set...');
  try {
    const response = await axios.get(`${WORMHOLESCAN_API}/guardianset/current`);
    const guardians = response.data.guardianSet.addresses.map((addr: string) => addr.toLowerCase());
    const guardianSetIndex = response.data.guardianSet.index;
    console.log(`Current Guardian Set Index: ${guardianSetIndex}`);
    console.log(`Number of guardians: ${guardians.length}`);
    return [guardians, guardianSetIndex];
  } catch (error: any) {
    console.error('❌ Error fetching guardian set:', error.message);
    return [[], -1];
  }
}

async function replaceSignatures(vaa: string | Uint8Array, observations: any[], currentGuardians: string[], guardianSetIndex: number) {
  console.log('\n🔄 Replacing signatures...');
  
  try {
    if (!vaa) throw new Error('VAA is undefined or empty.');
    if (currentGuardians.length === 0) throw new Error('Guardian set is empty.');
    if (observations.length === 0) throw new Error('No observations provided.');
    
    const validSigs = observations.filter((sig) => currentGuardians.includes(sig.guardianAddr));
    if (validSigs.length === 0) throw new Error('No valid signatures found. Cannot proceed.');
    
    console.log(`Found ${validSigs.length} valid signatures from current guardians`);
    
    const formattedSigs = validSigs
      .map((sig) => {
        try {
          const sigBuffer = Buffer.from(sig.signature, 'base64');
          const sigBuffer1 = sigBuffer.length === 130 ? Buffer.from(sigBuffer.toString(), 'hex') : sigBuffer;
          
          const r = BigInt('0x' + sigBuffer1.subarray(0, 32).toString('hex'));
          const s = BigInt('0x' + sigBuffer1.subarray(32, 64).toString('hex'));
          const vRaw = sigBuffer1[64];
          const v = vRaw < 27 ? vRaw : vRaw - 27;
          
          return {
            guardianIndex: currentGuardians.indexOf(sig.guardianAddr),
            signature: new Signature(r, s, v),
          };
        } catch (error) {
          console.error(`Failed to process signature for guardian: ${sig.guardianAddr}`);
          return null;
        }
      })
      .filter((sig): sig is { guardianIndex: number; signature: Signature } => sig !== null);
    
    let parsedVaa: VAA<'Uint8Array'>;
    try {
      parsedVaa = deserialize('Uint8Array', vaa);
    } catch (error) {
      throw new Error(`Error deserializing VAA: ${error}`);
    }
    
    const outdatedGuardianIndexes = parsedVaa.signatures
      .filter((vaaSig) => !formattedSigs.some((sig) => sig.guardianIndex === vaaSig.guardianIndex))
      .map((sig) => sig.guardianIndex);
    
    console.log('Outdated Guardian Indexes:', outdatedGuardianIndexes);
    
    let updatedSignatures = parsedVaa.signatures.filter((sig) => !outdatedGuardianIndexes.includes(sig.guardianIndex));
    
    const validReplacements = formattedSigs.filter((sig) => !updatedSignatures.some((s) => s.guardianIndex === sig.guardianIndex));
    
    if (outdatedGuardianIndexes.length > validReplacements.length) {
      console.warn(`Not enough valid replacement signatures! Need ${outdatedGuardianIndexes.length}, but only ${validReplacements.length} available.`);
      return null;
    }
    
    updatedSignatures = [...updatedSignatures, ...validReplacements.slice(0, outdatedGuardianIndexes.length)];
    updatedSignatures.sort((a, b) => a.guardianIndex - b.guardianIndex);
    
    const updatedVaa: VAA<'Uint8Array'> = {
      ...parsedVaa,
      guardianSet: guardianSetIndex,
      signatures: updatedSignatures,
    };
    
    let patchedVaa: Uint8Array;
    try {
      patchedVaa = serialize(updatedVaa);
    } catch (error) {
      throw new Error(`Error serializing updated VAA: ${error}`);
    }
    
    const vaaHex = `0x${Buffer.from(patchedVaa).toString('hex')}`;
    console.log('\n✅ Successfully replaced signatures!');
    console.log('\n📄 NEW VAA (hex format - copy this):');
    console.log('─────────────────────────────────────────────');
    console.log(vaaHex);
    console.log('─────────────────────────────────────────────');
    
    return vaaHex;
  } catch (error: any) {
    console.error('❌ Error in replaceSignatures:', error.message);
    return null;
  }
}

async function main() {
  console.log('═══════════════════════════════════════════════');
  console.log('  🌀 Wormhole VAA Signature Replacement');
  console.log('  Based on Official Wormhole Documentation');
  console.log('═══════════════════════════════════════════════\n');
  
  const vaaBytes = await fetchVaa(VAA_ID);
  if (!vaaBytes) {
    console.log('\n❌ Could not fetch VAA. Exiting.');
    process.exit(1);
  }
  
  const { valid } = await checkVaaValidity(vaaBytes);
  if (valid) {
    console.log('\n✅ VAA is already valid! No replacement needed.');
    const vaaHex = '0x' + Buffer.from(vaaBytes, 'base64').toString('hex');
    console.log('\n📄 VAA (hex):');
    console.log(vaaHex);
    return;
  }
  
  const observations = await fetchObservations(VAA_ID);
  if (observations.length === 0) {
    console.log('\n❌ No observations found. Cannot replace signatures.');
    process.exit(1);
  }
  
  const [currentGuardians, guardianSetIndex] = await fetchGuardianSet();
  if (currentGuardians.length === 0) {
    console.log('\n❌ Could not fetch guardian set. Exiting.');
    process.exit(1);
  }
  
  const newVaa = await replaceSignatures(Buffer.from(vaaBytes, 'base64'), observations, currentGuardians, guardianSetIndex);
  
  if (newVaa) {
    console.log('\n📋 Next steps:');
    console.log('   1. Copy the VAA hex string above');
    console.log('   2. Go to: https://arbiscan.io/address/0xa5f208e072434bC67592E4C49C1f9952Cf67E6a3#writeProxy');
    console.log('   3. Connect your wallet');
    console.log('   4. Call completeTransfer() with the new VAA');
    console.log('   5. Submit the transaction');
  }
}

main().catch(console.error);
