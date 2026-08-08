// Self-contained vanilla JS booking widget (green)
// Features: floating button, booking form panel, confirmation state, API integration
// Positioned BELOW the chatbot (mauve) button: green at bottom:20px, mauve at bottom:92px

(function() {
  // Configuration
  const config = {
    backendUrl: 'https://jcode-site-generator.onrender.com/booking',
    colors: {
      primary: '#10b981',
      secondary: '#34d399',
      headerGradient: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
      bg: '#1e293b',
      bubble: '#334155',
      textLight: '#ffffff',
      textDark: '#e2e8f0',
      label: '#94a3b8'
    },
    dimensions: {
      buttonSize: '60px',
      panelWidth: '340px',
      panelHeight: 'auto',
      maxPanelHeight: '560px'
    },
    services: ['Site web', 'Chatbot IA', 'Réservation Auto', 'Marketing automatisé', 'Autre']
  };

  // State
  let isOpen = false;

  // Create DOM elements
  function createElements() {
    // Floating button (green, bottom position)
    const button = document.createElement('button');
    button.id = 'jcode-booking-button';
    button.style.position = 'fixed';
    button.style.bottom = '20px';
    button.style.right = '20px';
    button.style.width = config.dimensions.buttonSize;
    button.style.height = config.dimensions.buttonSize;
    button.style.borderRadius = '50%';
    button.style.background = config.colors.headerGradient;
    button.style.color = '#fff';
    button.style.border = 'none';
    button.style.cursor = 'pointer';
    button.style.zIndex = '10001';
    button.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.35)';
    button.style.display = 'flex';
    button.style.alignItems = 'center';
    button.style.justifyContent = 'center';
    button.style.fontSize = '24px';
    button.innerHTML = '📅';
    button.title = 'Réserver une démo';
    button.setAttribute('aria-label', 'Ouvrir le formulaire de réservation');

    // Booking panel (opens above the mauve button: 20 + 60 + 60 + 24)
    const panel = document.createElement('div');
    panel.id = 'jcode-booking-window';
    panel.style.position = 'fixed';
    panel.style.bottom = '164px';
    panel.style.right = '20px';
    panel.style.width = config.dimensions.panelWidth;
    panel.style.height = config.dimensions.panelHeight;
    panel.style.maxHeight = config.dimensions.maxPanelHeight;
    panel.style.backgroundColor = config.colors.bg;
    panel.style.borderRadius = '16px';
    panel.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.2)';
    panel.style.display = 'none';
    panel.style.flexDirection = 'column';
    panel.style.overflow = 'hidden';
    panel.style.zIndex = '10002';
    panel.style.border = '1px solid rgba(255,255,255,0.08)';

    // Header
    const header = document.createElement('div');
    header.style.padding = '16px';
    header.style.background = config.colors.headerGradient;
    header.style.color = '#fff';
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';

    const headerTitleWrap = document.createElement('div');
    headerTitleWrap.style.display = 'flex';
    headerTitleWrap.style.alignItems = 'center';
    headerTitleWrap.style.gap = '8px';

    const statusDot = document.createElement('span');
    statusDot.style.width = '8px';
    statusDot.style.height = '8px';
    statusDot.style.borderRadius = '50%';
    statusDot.style.background = '#22c55e';

    const title = document.createElement('h3');
    title.textContent = 'Réservation Auto';
    title.style.margin = '0';
    title.style.fontSize = '16px';
    title.style.fontWeight = '600';

    headerTitleWrap.appendChild(statusDot);
    headerTitleWrap.appendChild(title);

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '✕';
    closeBtn.style.background = 'transparent';
    closeBtn.style.border = 'none';
    closeBtn.style.color = '#fff';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.fontSize = '18px';
    closeBtn.title = 'Fermer';
    closeBtn.addEventListener('click', togglePanel);

    header.appendChild(headerTitleWrap);
    header.appendChild(closeBtn);

    // Form area
    const formArea = document.createElement('div');
    formArea.id = 'jcode-booking-form';
    formArea.style.padding = '16px';
    formArea.style.display = 'flex';
    formArea.style.flexDirection = 'column';
    formArea.style.gap = '12px';
    formArea.style.overflowY = 'auto';

    // Field helper
    function createLabel(text) {
      const label = document.createElement('label');
      label.textContent = text;
      label.style.display = 'block';
      label.style.fontSize = '11px';
      label.style.fontWeight = '600';
      label.style.color = config.colors.label;
      label.style.marginBottom = '4px';
      return label;
    }

    function createInput(type, placeholder) {
      const input = document.createElement('input');
      input.type = type;
      input.placeholder = placeholder || '';
      input.style.width = '100%';
      input.style.padding = '10px 12px';
      input.style.background = 'rgba(255,255,255,0.05)';
      input.style.border = '1px solid rgba(255,255,255,0.1)';
      input.style.borderRadius = '8px';
      input.style.color = config.colors.textDark;
      input.style.fontSize = '13px';
      input.style.boxSizing = 'border-box';
      input.style.outline = 'none';
      return input;
    }

    function createSelect(options) {
      const select = document.createElement('select');
      select.style.width = '100%';
      select.style.padding = '10px 12px';
      select.style.background = '#334155';
      select.style.border = '1px solid rgba(255,255,255,0.1)';
      select.style.borderRadius = '8px';
      select.style.color = config.colors.textDark;
      select.style.fontSize = '13px';
      select.style.boxSizing = 'border-box';
      select.style.outline = 'none';
      options.forEach(function(opt) {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        option.style.background = '#1e293b';
        option.style.color = '#e2e8f0';
        select.appendChild(option);
      });
      return select;
    }

    // Service
    const serviceWrap = document.createElement('div');
    serviceWrap.appendChild(createLabel('Service'));
    const serviceSelect = createSelect(config.services);
    serviceWrap.appendChild(serviceSelect);

    // Date
    const dateWrap = document.createElement('div');
    dateWrap.appendChild(createLabel('Date'));
    const dateInput = createInput('date');
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    dateInput.min = todayStr;
    dateWrap.appendChild(dateInput);

    // Heure
    const timeWrap = document.createElement('div');
    timeWrap.appendChild(createLabel('Heure'));
    const timeInput = createInput('time');
    timeInput.min = '09:00';
    timeInput.max = '20:00';
    timeWrap.appendChild(timeInput);

    // Nom
    const nameWrap = document.createElement('div');
    nameWrap.appendChild(createLabel('Nom'));
    const nameInput = createInput('text', 'Votre nom');
    nameWrap.appendChild(nameInput);

    // Email
    const emailWrap = document.createElement('div');
    emailWrap.appendChild(createLabel('Email'));
    const emailInput = createInput('email', 'votre@email.com');
    emailWrap.appendChild(emailInput);

    // Téléphone
    const phoneWrap = document.createElement('div');
    phoneWrap.appendChild(createLabel('Téléphone'));
    const phoneInput = createInput('tel', '0470/00.00.00');
    phoneWrap.appendChild(phoneInput);

    // Submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'button';
    submitBtn.textContent = 'Confirmer la réservation';
    submitBtn.style.width = '100%';
    submitBtn.style.padding = '12px';
    submitBtn.style.background = config.colors.headerGradient;
    submitBtn.style.color = '#fff';
    submitBtn.style.border = 'none';
    submitBtn.style.borderRadius = '8px';
    submitBtn.style.fontSize = '14px';
    submitBtn.style.fontWeight = '600';
    submitBtn.style.cursor = 'pointer';
    submitBtn.addEventListener('click', function() {
      submitBooking();
    });

    formArea.appendChild(serviceWrap);
    formArea.appendChild(dateWrap);
    formArea.appendChild(timeWrap);
    formArea.appendChild(nameWrap);
    formArea.appendChild(emailWrap);
    formArea.appendChild(phoneWrap);
    formArea.appendChild(submitBtn);

    // Confirmation state (hidden by default)
    const confirmation = document.createElement('div');
    confirmation.id = 'jcode-booking-confirmation';
    confirmation.style.display = 'none';
    confirmation.style.padding = '24px 16px';
    confirmation.style.textAlign = 'center';
    confirmation.style.flexDirection = 'column';
    confirmation.style.gap = '12px';

    const confirmIcon = document.createElement('div');
    confirmIcon.style.fontSize = '36px';
    confirmIcon.textContent = '✅';

    const confirmTitle = document.createElement('div');
    confirmTitle.textContent = 'Réservation confirmée';
    confirmTitle.style.color = '#34d399';
    confirmTitle.style.fontSize = '16px';
    confirmTitle.style.fontWeight = '700';

    const confirmSummary = document.createElement('div');
    confirmSummary.id = 'jcode-booking-summary';
    confirmSummary.style.color = config.colors.label;
    confirmSummary.style.fontSize = '12px';
    confirmSummary.style.lineHeight = '1.6';

    const confirmNote = document.createElement('div');
    confirmNote.style.color = config.colors.label;
    confirmNote.style.fontSize = '11px';
    confirmNote.style.lineHeight = '1.5';
    confirmNote.textContent = 'Un email de confirmation vient de vous être envoyé. Nous vous recontactons très vite !';

    const confirmClose = document.createElement('button');
    confirmClose.textContent = 'Fermer';
    confirmClose.style.padding = '10px 20px';
    confirmClose.style.background = 'rgba(255,255,255,0.08)';
    confirmClose.style.color = '#fff';
    confirmClose.style.border = '1px solid rgba(255,255,255,0.15)';
    confirmClose.style.borderRadius = '8px';
    confirmClose.style.fontSize = '13px';
    confirmClose.style.cursor = 'pointer';
    confirmClose.addEventListener('click', togglePanel);

    confirmation.appendChild(confirmIcon);
    confirmation.appendChild(confirmTitle);
    confirmation.appendChild(confirmSummary);
    confirmation.appendChild(confirmNote);
    confirmation.appendChild(confirmClose);

    // Assemble panel
    panel.appendChild(header);
    panel.appendChild(formArea);
    panel.appendChild(confirmation);

    // Add to body
    document.body.appendChild(button);
    document.body.appendChild(panel);

    // Event listeners
    button.addEventListener('click', togglePanel);

    // Mobile responsiveness
    function handleResize() {
      if (window.innerWidth <= 480) {
        panel.style.width = 'calc(100% - 40px)';
        panel.style.left = '20px';
        panel.style.right = '20px';
        panel.style.maxHeight = '70vh';
      } else {
        panel.style.width = config.dimensions.panelWidth;
        panel.style.left = 'auto';
        panel.style.right = '20px';
        panel.style.maxHeight = config.dimensions.maxPanelHeight;
      }
    }

    window.addEventListener('resize', handleResize);
    handleResize();
  }

  // Toggle panel open/close
  function togglePanel() {
    const panel = document.getElementById('jcode-booking-window');
    isOpen = !isOpen;
    if (isOpen) {
      panel.style.display = 'flex';
    } else {
      panel.style.display = 'none';
    }
  }

  // Show confirmation state
  function showConfirmation(summaryText) {
    const formArea = document.getElementById('jcode-booking-form');
    const confirmation = document.getElementById('jcode-booking-confirmation');
    const summary = document.getElementById('jcode-booking-summary');
    formArea.style.display = 'none';
    confirmation.style.display = 'flex';
    summary.textContent = summaryText;
  }

  // Submit booking to backend
  function submitBooking() {
    const service = document.querySelector('#jcode-booking-window select').value;
    const date = document.querySelector('#jcode-booking-window input[type="date"]').value;
    const time = document.querySelector('#jcode-booking-window input[type="time"]').value;
    const name = document.querySelector('#jcode-booking-window input[type="text"]').value;
    const email = document.querySelector('#jcode-booking-window input[type="email"]').value;
    const phone = document.querySelector('#jcode-booking-window input[type="tel"]').value;

    if (!service || !date || !time || !name || !email) {
      alert('Merci de remplir tous les champs (Service, Date, Heure, Nom, Email).');
      return;
    }

    const submitBtn = document.querySelector('#jcode-booking-window button[type="button"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Envoi en cours...';

    const payload = {
      service: service,
      date: date,
      time: time,
      name: name,
      email: email,
      phone: phone,
      client: 'jcode'
    };

    fetch(config.backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'ok') {
        const summary = service + ' — ' + date + ' à ' + time;
        showConfirmation(summary);
      } else {
        alert(data.message || 'Erreur lors de la réservation. Veuillez réessayer.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Confirmer la réservation';
      }
    })
    .catch(function() {
      alert('Erreur de connexion. Veuillez réessayer.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Confirmer la réservation';
    });
  }

  // Initialize the widget
  function init() {
    if (document.getElementById('jcode-booking-button')) {
      return;
    }
    createElements();
  }

  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
