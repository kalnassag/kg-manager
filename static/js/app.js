/**
 * Product Knowledge Graph Manager - Client-side JavaScript
 */

// Store user preferences in localStorage
const Preferences = {
    VIEW_MODE_KEY: 'kg_view_mode',

    getViewMode() {
        return localStorage.getItem(this.VIEW_MODE_KEY) || 'list';
    },

    setViewMode(mode) {
        localStorage.setItem(this.VIEW_MODE_KEY, mode);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Store view mode when toggling
    const viewBtns = document.querySelectorAll('.view-btn');
    viewBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const url = new URL(this.href);
            const viewMode = url.searchParams.get('view');
            if (viewMode) {
                Preferences.setViewMode(viewMode);
            }
        });
    });

    // Confirm delete actions
    const deleteForms = document.querySelectorAll('form[action*="/delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this entity? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-focus search inputs
    const searchInputs = document.querySelectorAll('.search-input[autofocus]');
    if (searchInputs.length > 0) {
        searchInputs[0].focus();
    }

    // Form validation
    const forms = document.querySelectorAll('.entity-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value || field.value.trim() === '') {
                    isValid = false;
                    field.style.borderColor = 'var(--danger)';
                } else {
                    field.style.borderColor = 'var(--border)';
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Clear field validation error on input
    const inputs = document.querySelectorAll('input[required]');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value && this.value.trim() !== '') {
                this.style.borderColor = 'var(--border)';
            }
        });
    });
});

// Utility functions
function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? 'var(--success)' : 'var(--primary-blue)'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
