// A tall sidebar moves with the page until its bottom is visible; no nested scroll.
const panels = document.querySelectorAll('.workspace > aside, .bank-layout > aside');
const measure = () => panels.forEach(panel => panel.style.setProperty('--sidebar-height', `${panel.getBoundingClientRect().height}px`));
const observer = new ResizeObserver(measure);
panels.forEach(panel => observer.observe(panel));
measure();
