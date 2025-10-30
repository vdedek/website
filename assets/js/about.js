// Rain effect
const MAX_RAINDROPS = 100;
let activeRaindrops = 0;

function createRaindrop() {
  if (activeRaindrops >= MAX_RAINDROPS) return;
  
  const raindrop = document.createElement('div');
  raindrop.className = 'raindrop';
  raindrop.style.left = Math.random() * window.innerWidth + 'px';
  raindrop.style.animationDuration = (Math.random() * 0.2 + 0.3) + 's';
  document.getElementById('rainContainer').appendChild(raindrop);
  activeRaindrops++;
  
  // Remove the raindrop after animation
  const removeRaindrop = () => {
    if (raindrop.parentElement) {
      raindrop.remove();
      activeRaindrops--;
    }
  };
  
  raindrop.addEventListener('animationend', removeRaindrop);
  // Fallback cleanup in case animation event doesn't fire
  setTimeout(removeRaindrop, 1000);
}

// Create two raindrops every 50ms
function createRaindrops() {
  createRaindrop();
  createRaindrop();
}

setInterval(createRaindrops, 50);

// Navigation hide/show on scroll
let lastScrollTop = 0;
let scrollTimeout;
let isFirstScroll = true;

function handleNavVisibility() {
  const navArea = document.querySelector('.nav-area');
  const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
  
  // Skip the first scroll event after page load
  if (isFirstScroll) {
    isFirstScroll = false;
    lastScrollTop = currentScroll;
    return;
  }
  
  // Only hide if we've scrolled down significantly
  if (currentScroll > lastScrollTop && currentScroll > 50) {
    // Scrolling down
    navArea.classList.add('hidden');
  } else if (currentScroll < lastScrollTop) {
    // Scrolling up
    navArea.classList.remove('hidden');
  }
  
  lastScrollTop = currentScroll;
}

// Throttle scroll events
window.addEventListener('scroll', () => {
  if (!scrollTimeout) {
    scrollTimeout = setTimeout(() => {
      handleNavVisibility();
      scrollTimeout = null;
    }, 100);
  }
});

// Toggle sections functionality
document.addEventListener('DOMContentLoaded', function() {
  const toggleButtons = document.querySelectorAll('.toggle-button');
  const allRows = document.querySelectorAll('tr[data-section]');
  
  // Initially hide all section rows
  allRows.forEach(row => {
    row.style.display = 'none';
  });
  
  // Handle toggle button clicks
  toggleButtons.forEach(button => {
    button.addEventListener('click', function() {
      const sectionName = this.dataset.section;
      const sectionRows = document.querySelectorAll(`tr[data-section="${sectionName}"]`);
      const isCurrentlyHidden = sectionRows[0].style.display === 'none';
      
      if (isCurrentlyHidden) {
        // Show rows
        sectionRows.forEach(row => {
          row.style.display = '';
        });
        // Change arrow to up
        this.textContent = '▲';
      } else {
        // Hide rows
        sectionRows.forEach(row => {
          row.style.display = 'none';
        });
        // Change arrow to down
        this.textContent = '▼';
      }
    });
  });
});
