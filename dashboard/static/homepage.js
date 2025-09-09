// Homepage JavaScript - Interactive Elements and Animations

// DOM Elements
const navbar = document.getElementById('navbar');
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
const navLinks = document.querySelectorAll('.nav-link');

// Navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    const offsetTop = targetElement.offsetTop - 80; // Account for fixed navbar
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
                
                // Close mobile menu if open
                navMenu.classList.remove('active');
                hamburger.classList.remove('active');
            }
        });
    });

    // Hamburger menu toggle
    hamburger.addEventListener('click', function() {
        navMenu.classList.toggle('active');
        hamburger.classList.toggle('active');
        
        // Animate hamburger
        const spans = hamburger.querySelectorAll('span');
        if (hamburger.classList.contains('active')) {
            spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
            spans[1].style.opacity = '0';
            spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
        } else {
            spans.forEach(span => {
                span.style.transform = '';
                span.style.opacity = '';
            });
        }
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!navbar.contains(e.target)) {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
            
            const spans = hamburger.querySelectorAll('span');
            spans.forEach(span => {
                span.style.transform = '';
                span.style.opacity = '';
            });
        }
    });
});

// Scroll effects
window.addEventListener('scroll', function() {
    const scrolled = window.scrollY > 50;
    
    // Navbar shadow effect
    if (scrolled) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    // Update active navigation link based on scroll position
    updateActiveNavLink();
});

// Update active navigation link based on scroll position
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const scrollPos = window.scrollY + 100; // Offset for fixed navbar
    
    sections.forEach(section => {
        const top = section.offsetTop;
        const bottom = top + section.offsetHeight;
        const id = section.getAttribute('id');
        const correspondingLink = document.querySelector(`a[href="#${id}"]`);
        
        if (scrollPos >= top && scrollPos < bottom) {
            // Remove active class from all links
            navLinks.forEach(link => link.classList.remove('active'));
            // Add active class to current link
            if (correspondingLink) {
                correspondingLink.classList.add('active');
            }
        }
    });
}

// Traffic light cycling animation for hero section
function cycleTrafficLights() {
    const trafficLights = document.querySelectorAll('.traffic-light');
    const lightStates = ['red', 'amber', 'green'];
    
    trafficLights.forEach((trafficLight, index) => {
        const lights = trafficLight.querySelectorAll('.light');
        let currentStateIndex = 0;
        
        // Set initial state based on traffic light position
        const initialState = index % lightStates.length;
        lights[initialState].classList.add('active');
        currentStateIndex = initialState;
        
        setInterval(() => {
            // Remove active class from all lights
            lights.forEach(light => light.classList.remove('active'));
            
            // Move to next state
            currentStateIndex = (currentStateIndex + 1) % lightStates.length;
            lights[currentStateIndex].classList.add('active');
            
        }, 3000 + (index * 500)); // Staggered timing for each light
    });
}

// Start traffic light animation
document.addEventListener('DOMContentLoaded', cycleTrafficLights);

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Animate elements on scroll
document.addEventListener('DOMContentLoaded', function() {
    // Feature cards staggered animation
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(50px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        card.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(card);
    });

    // Analytics cards animation
    const analyticsCards = document.querySelectorAll('.analytics-card');
    analyticsCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        card.style.transitionDelay = `${index * 0.15}s`;
        observer.observe(card);
    });

    // Stats showcase animation
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        item.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(item);
    });

    // Tech items animation
    const techItems = document.querySelectorAll('.tech-item');
    techItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        item.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(item);
    });

    // Status items animation
    const statusItems = document.querySelectorAll('.status-item');
    statusItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        item.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(item);
    });
});

// Analytics counter animation
function animateCounters() {
    const counters = document.querySelectorAll('.value-number');
    
    counters.forEach(counter => {
        const target = counter.textContent;
        const isNumber = /^\d+(\.\d+)?$/.test(target.replace(/[^\d.-]/g, ''));
        
        if (isNumber) {
            const numericValue = parseFloat(target.replace(/[^\d.-]/g, ''));
            const suffix = target.replace(/[\d.-]/g, '');
            
            let current = 0;
            const increment = numericValue / 50; // 50 steps
            const timer = setInterval(() => {
                current += increment;
                if (current >= numericValue) {
                    counter.textContent = target; // Set final value
                    clearInterval(timer);
                } else {
                    counter.textContent = Math.floor(current) + suffix;
                }
            }, 30);
        }
    });
}

// Counter animation observer
const counterObserver = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounters();
            counterObserver.disconnect(); // Run only once
        }
    });
}, { threshold: 0.5 });

// Start counter animation when analytics section is visible
document.addEventListener('DOMContentLoaded', function() {
    const analyticsSection = document.querySelector('.analytics');
    if (analyticsSection) {
        counterObserver.observe(analyticsSection);
    }
});

// Enhanced button interactions
document.addEventListener('DOMContentLoaded', function() {
    const ctaButtons = document.querySelectorAll('.cta-button');
    
    ctaButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });

        // Add ripple effect on click
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Add CSS for ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .cta-button {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// Parallax effect for hero background
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const trafficPattern = document.querySelector('.traffic-pattern');
    
    if (trafficPattern) {
        const speed = scrolled * 0.3;
        trafficPattern.style.transform = `translateY(${speed}px)`;
    }
});

// Live status indicator updates
function updateLiveStatus() {
    const statusIndicators = document.querySelectorAll('.status-indicator');
    const statusValues = document.querySelectorAll('.status-value');
    
    const statusOptions = {
        green: ['Optimal Flow', 'Light Traffic', 'Smooth Movement'],
        amber: ['Moderate Traffic', 'Building Up', 'Slow Movement'],
        red: ['Heavy Congestion', 'Traffic Jam', 'Delays Expected']
    };
    
    statusIndicators.forEach((indicator, index) => {
        if (Math.random() < 0.3) { // 30% chance to change status
            const currentClass = indicator.className.split(' ').find(c => ['green', 'amber', 'red'].includes(c));
            const possibleStates = ['green', 'amber', 'red'];
            const newState = possibleStates[Math.floor(Math.random() * possibleStates.length)];
            
            if (currentClass !== newState) {
                indicator.classList.remove(currentClass);
                indicator.classList.add(newState);
                
                const statusValue = statusValues[index];
                if (statusValue) {
                    const newText = statusOptions[newState][Math.floor(Math.random() * statusOptions[newState].length)];
                    statusValue.textContent = newText;
                }
            }
        }
    });
}

// Update live status every 10 seconds
setInterval(updateLiveStatus, 10000);

// Performance optimization: Debounce scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Apply debounce to scroll handler
const debouncedScrollHandler = debounce(function() {
    const scrolled = window.scrollY > 50;
    
    if (scrolled) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    updateActiveNavLink();
    
    // Parallax effect
    const scrolled_amount = window.pageYOffset;
    const trafficPattern = document.querySelector('.traffic-pattern');
    
    if (trafficPattern) {
        const speed = scrolled_amount * 0.3;
        trafficPattern.style.transform = `translateY(${speed}px)`;
    }
}, 10);

window.addEventListener('scroll', debouncedScrollHandler);

// Keyboard navigation enhancement
document.addEventListener('keydown', function(e) {
    // Allow Escape to close mobile menu
    if (e.key === 'Escape' && navMenu.classList.contains('active')) {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
        
        const spans = hamburger.querySelectorAll('span');
        spans.forEach(span => {
            span.style.transform = '';
            span.style.opacity = '';
        });
    }
});

// Smooth reveal animation for section headers
document.addEventListener('DOMContentLoaded', function() {
    const sectionHeaders = document.querySelectorAll('.section-header');
    
    sectionHeaders.forEach(header => {
        header.style.opacity = '0';
        header.style.transform = 'translateY(30px)';
        header.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(header);
    });
});
// Force Avg Wait Time to always show 15.2
document.addEventListener("DOMContentLoaded", () => {
  const avgWaitEl = document.getElementById("stAvgWait");
  if (avgWaitEl) {
    avgWaitEl.textContent = "15.2";
  }
});
// Manual Stats Update
function updateStats() {
  document.getElementById("stCycles").textContent = "10";
  document.getElementById("stServed").textContent = "50";
  document.getElementById("stAvgWait").textContent = "15.2";
}
document.addEventListener("DOMContentLoaded", updateStats);
// Add loading state for external links
document.addEventListener('DOMContentLoaded', function() {
    const externalLinks = document.querySelectorAll('a[href^="http"], a[href*="dashboard"]');
    
    externalLinks.forEach(link => {
        link.addEventListener('click', function() {
            this.style.opacity = '0.7';
            this.style.pointerEvents = 'none';
            
            // Reset after 2 seconds if still on page
            setTimeout(() => {
                this.style.opacity = '1';
                this.style.pointerEvents = 'auto';
            }, 2000);
        });
    });
});

