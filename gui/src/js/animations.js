/**
 * Animations for Luna Gaming Tool
 * 
 * This module provides animations for UI elements.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Add animation classes to elements
  setupAnimations();
  
  // Set up observers for dynamic content
  setupObservers();
});

/**
 * Set up animations for static elements
 */
function setupAnimations() {
  // Add fade-in animation to cards
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    
    // Stagger the animations
    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 100 * index);
  });
  
  // Add hover effects to buttons
  const buttons = document.querySelectorAll('.btn');
  buttons.forEach(button => {
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'scale(1.05)';
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'scale(1)';
    });
  });
  
  // Add ripple effect to buttons
  buttons.forEach(button => {
    button.addEventListener('click', createRipple);
  });
}

/**
 * Create ripple effect on button click
 * @param {Event} e - Click event
 */
function createRipple(e) {
  const button = e.currentTarget;
  
  const circle = document.createElement('span');
  const diameter = Math.max(button.clientWidth, button.clientHeight);
  const radius = diameter / 2;
  
  circle.style.width = circle.style.height = `${diameter}px`;
  circle.style.left = `${e.clientX - button.offsetLeft - radius}px`;
  circle.style.top = `${e.clientY - button.offsetTop - radius}px`;
  circle.classList.add('ripple');
  
  const ripple = button.querySelector('.ripple');
  if (ripple) {
    ripple.remove();
  }
  
  button.appendChild(circle);
}

/**
 * Set up observers for dynamic content
 */
function setupObservers() {
  // Observe activity list for changes
  const activityList = document.getElementById('activity-list');
  if (activityList) {
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          // Animate new activity items
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1) { // Element node
              animateActivityItem(node);
            }
          });
        }
      });
    });
    
    observer.observe(activityList, { childList: true });
  }
}

/**
 * Animate activity item
 * @param {HTMLElement} item - Activity item element
 */
function animateActivityItem(item) {
  item.style.opacity = '0';
  item.style.transform = 'translateX(20px)';
  item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
  
  setTimeout(() => {
    item.style.opacity = '1';
    item.style.transform = 'translateX(0)';
  }, 10);
}

// Add ripple styles to document
const style = document.createElement('style');
style.textContent = `
  .btn {
    position: relative;
    overflow: hidden;
  }
  
  .ripple {
    position: absolute;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.4);
    transform: scale(0);
    animation: ripple 0.6s linear;
    pointer-events: none;
  }
  
  @keyframes ripple {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);