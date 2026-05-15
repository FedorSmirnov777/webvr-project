const faqItems = Array.from(document.querySelectorAll(".cs-faq-item"));

for (const item of faqItems) {
  const button = item.querySelector(".cs-button");
  if (!button) continue;

  const onClick = (event) => {
    event.stopPropagation();
    item.classList.toggle("active");
  };

  button.addEventListener("click", onClick);
}
