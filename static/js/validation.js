function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showError(el, msg) {
  let err = el.parentNode.querySelector('.field-error');
  if (!err) {
    err = document.createElement('div');
    err.className = 'field-error';
    err.style.cssText = 'color:var(--danger);font-size:11px;margin-top:4px;';
    el.parentNode.appendChild(err);
  }
  err.textContent = msg;
  el.style.borderColor = 'var(--danger)';
}

function clearError(el) {
  const err = el.parentNode.querySelector('.field-error');
  if (err) err.remove();
  el.style.borderColor = '';
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.form-control').forEach(el => {
    el.addEventListener('blur', () => {
      if (el.type === 'email' && el.value && !validateEmail(el.value))
        showError(el, 'Please enter a valid email address.');
      else if (el.type === 'password' && el.value && el.value.length < 6)
        showError(el, 'Password must be at least 6 characters.');
      else clearError(el);
    });
    el.addEventListener('input', () => clearError(el));
  });
});