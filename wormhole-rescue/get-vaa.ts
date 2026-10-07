import axios from 'axios';

const WORMHOLESCAN_API = 'https://api.wormholescan.io/v1';
const VAA_ID = '4/000000000000000000000000b6f6d86a8f9879a9c87f643768d9efc38c1da6e7/370072';

async function main() {
  console.log('Fetching VAA...');
  const response = await axios.get(WORMHOLESCAN_API + '/signed_vaa/' + VAA_ID);
  const vaaBytes = response.data.vaaBytes;
  const vaaHex = '0x' + Buffer.from(vaaBytes, 'base64').toString('hex');
  console.log('\nVAA (hex) - COPY THIS:');
  console.log('----------------------');
  console.log(vaaHex);
  console.log('----------------------');
}

main().catch(console.error);
