document.addEventListener('click', (e)=>{
  const btn = e.target.closest('button.copy');
  if (!btn) return;
  const text = btn.getAttribute('data-copy');
  if (!text) return;
  navigator.clipboard.writeText(text).then(()=>{
    const old = btn.textContent;
    btn.textContent = 'Copied';
    btn.classList.add('copied');
    setTimeout(()=>{ btn.textContent = old; btn.classList.remove('copied'); }, 1400);
  });
});

document.getElementById('year').textContent = new Date().getFullYear();
