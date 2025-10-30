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

// Filter and scroll functionality
document.addEventListener('DOMContentLoaded', function() {
  const filterCells = document.querySelectorAll('.filter-cell');
  const projectCells = document.querySelectorAll('.project-cell');
  const yearCells = document.querySelectorAll('.year-cell');
  const filterWrapper = document.querySelector('.filter-table-wrapper');
  const scrollLeft = document.querySelector('.scroll-left');
  const scrollRight = document.querySelector('.scroll-right');

  // Handle scroll indicators
  function updateScrollIndicators() {
    const maxScroll = filterWrapper.scrollWidth - filterWrapper.clientWidth;
    const scrollPosition = filterWrapper.scrollLeft;
    const filterTable = document.querySelector('.filter-table');
    const filterCell = document.querySelector('.filter-cell');
    const tableRect = filterTable.getBoundingClientRect();
    const cellRect = filterCell.getBoundingClientRect();
    
    // Update vertical position to match filter cell exactly
    scrollLeft.style.top = `${cellRect.top}px`;
    scrollRight.style.top = `${cellRect.top}px`;
    scrollLeft.style.height = `${cellRect.height}px`;
    scrollRight.style.height = `${cellRect.height}px`;
    
    // Show left gradient if we've scrolled right
    if (scrollPosition > 0) {
      scrollLeft.style.display = 'block';
      scrollLeft.style.opacity = Math.min(scrollPosition / 50, 0.8);
    } else {
      scrollLeft.style.display = 'none';
    }

    // Show right gradient if there's more content to scroll to
    const remainingScroll = maxScroll - scrollPosition;
    if (remainingScroll > 0) {
      scrollRight.style.display = 'block';
      scrollRight.style.opacity = Math.min(remainingScroll / 50, 0.8);
    } else {
      scrollRight.style.display = 'none';
    }
  }

  // Initial check
  updateScrollIndicators();

  // Update on scroll
  filterWrapper.addEventListener('scroll', updateScrollIndicators);

  // Update on resize and page scroll
  window.addEventListener('resize', updateScrollIndicators);
  window.addEventListener('scroll', updateScrollIndicators);

  // Function to update year rows visibility
  function updateYearVisibility(filter) {
    // First hide all year rows
    yearCells.forEach(yearCell => {
      yearCell.parentElement.style.display = 'none';
    });

    // Show years that have visible projects
    yearCells.forEach(yearCell => {
      let nextElement = yearCell.parentElement.nextElementSibling;
      let hasVisibleProjects = false;

      // Look through all projects until next year row or end
      while (nextElement && !nextElement.querySelector('.year-cell')) {
        if (nextElement.classList.contains('visible')) {
          hasVisibleProjects = true;
          break;
        }
        nextElement = nextElement.nextElementSibling;
      }

      // Show year row if it has visible projects
      if (hasVisibleProjects) {
        yearCell.parentElement.style.display = '';
      }
    });
  }

  // Handle filtering
  filterCells.forEach(cell => {
    cell.addEventListener('click', () => {
      // Remove active class from all cells
      filterCells.forEach(c => c.classList.remove('active'));
      
      // Add active class to clicked cell
      cell.classList.add('active');
    
      const filter = cell.dataset.filter;
    
      // Show/hide projects based on filter
      projectCells.forEach(project => {
        const categories = project.dataset.categories.split(' ');
        if (categories.includes(filter)) {
          project.classList.add('visible');
        } else {
          project.classList.remove('visible');
        }
      });

      // Update year rows visibility
      updateYearVisibility(filter);
    });
  });

  // Initial year visibility update for 'selected' filter
  updateYearVisibility('selected');

  // Add click handlers for project cells on mobile
  if (window.innerWidth <= 768) {
    projectCells.forEach(cell => {
      const title = cell.querySelector('.project-title').textContent;
      // Convert title to URL-friendly format
      const url = title.toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '') + '.html';
      
      cell.addEventListener('click', () => {
        window.location.href = url;
      });
    });
  }
}); 