/**
 * Üniversite Ders Kayıt Sistemi - Ana JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavigation();
    initFlashMessages();
    initDragAndDrop();
    initFormValidation();
    initConfirmDialogs();
    initTooltips();
    initSearchFilter();
});

/**
 * Mobile Navigation Toggle
 */
function initNavigation() {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            const icon = navToggle.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-bars');
                icon.classList.toggle('fa-times');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('active');
                const icon = navToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }
}

/**
 * Flash Messages - Auto-dismiss
 */
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(function(alert) {
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            dismissAlert(alert);
        }, 5000);
        
        // Close button
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                dismissAlert(alert);
            });
        }
    });
}

function dismissAlert(alert) {
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100%)';
    setTimeout(function() {
        alert.remove();
    }, 300);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-messages') || createFlashContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${getIconForType(type)}"></i>
        <span>${message}</span>
        <button class="alert-close">&times;</button>
    `;
    
    container.appendChild(alert);
    
    // Initialize dismiss behavior
    setTimeout(function() {
        dismissAlert(alert);
    }, 5000);
    
    alert.querySelector('.alert-close').addEventListener('click', function() {
        dismissAlert(alert);
    });
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'danger': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Drag and Drop for Cart Items
 */
function initDragAndDrop() {
    const cartContainer = document.querySelector('.cart-items');
    if (!cartContainer) return;
    
    const cartItems = cartContainer.querySelectorAll('.cart-item');
    
    cartItems.forEach(function(item) {
        const handle = item.querySelector('.cart-drag-handle');
        if (!handle) return;
        
        handle.addEventListener('mousedown', function() {
            item.setAttribute('draggable', 'true');
        });
        
        item.addEventListener('dragstart', function(e) {
            item.classList.add('dragging');
            e.dataTransfer.setData('text/plain', item.dataset.courseId);
        });
        
        item.addEventListener('dragend', function() {
            item.classList.remove('dragging');
            item.removeAttribute('draggable');
            updateCartOrder();
        });
        
        item.addEventListener('dragover', function(e) {
            e.preventDefault();
            const dragging = document.querySelector('.dragging');
            if (dragging && dragging !== item) {
                const rect = item.getBoundingClientRect();
                const midY = rect.top + rect.height / 2;
                if (e.clientY < midY) {
                    cartContainer.insertBefore(dragging, item);
                } else {
                    cartContainer.insertBefore(dragging, item.nextSibling);
                }
            }
        });
    });
}

function updateCartOrder() {
    const cartItems = document.querySelectorAll('.cart-item');
    const orders = [];
    
    cartItems.forEach(function(item, index) {
        const orderBadge = item.querySelector('.cart-order');
        if (orderBadge) {
            orderBadge.textContent = index + 1;
        }
        orders.push({
            course_id: item.dataset.courseId,
            order: index + 1
        });
    });
    
    // Send to server
    fetch('/api/cart/reorder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ orders: orders })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Sıralama güncellendi', 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Sıralama güncellenemedi', 'error');
    });
}

/**
 * Form Validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    showFieldError(field, 'Bu alan zorunludur');
                } else {
                    clearFieldError(field);
                }
            });
            
            // Email validation
            const emailFields = form.querySelectorAll('input[type="email"]');
            emailFields.forEach(function(field) {
                if (field.value && !isValidEmail(field.value)) {
                    isValid = false;
                    showFieldError(field, 'Geçerli bir e-posta adresi girin');
                }
            });
            
            // Password match
            const password = form.querySelector('input[name="password"]');
            const confirmPassword = form.querySelector('input[name="confirm_password"]');
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                isValid = false;
                showFieldError(confirmPassword, 'Şifreler eşleşmiyor');
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

function showFieldError(field, message) {
    clearFieldError(field);
    field.classList.add('is-invalid');
    
    const error = document.createElement('div');
    error.className = 'field-error text-danger';
    error.style.fontSize = '0.8125rem';
    error.style.marginTop = '0.25rem';
    error.textContent = message;
    
    field.parentNode.appendChild(error);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const error = field.parentNode.querySelector('.field-error');
    if (error) {
        error.remove();
    }
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Confirm Dialogs
 */
function initConfirmDialogs() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = button.dataset.confirm || 'Bu işlemi gerçekleştirmek istediğinizden emin misiniz?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Tooltips
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(function(element) {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = element.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: #1e293b;
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: 0.375rem;
                font-size: 0.75rem;
                z-index: 1000;
                max-width: 200px;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + window.scrollY + 'px';
            
            element._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (element._tooltip) {
                element._tooltip.remove();
                element._tooltip = null;
            }
        });
    });
}

/**
 * Search and Filter
 */
function initSearchFilter() {
    const searchInput = document.querySelector('.search-input');
    const filterSelect = document.querySelectorAll('.filter-select');
    
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                applyFilters();
            }, 300);
        });
    }
    
    filterSelect.forEach(function(select) {
        select.addEventListener('change', applyFilters);
    });
}

function applyFilters() {
    const searchInput = document.querySelector('.search-input');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    const items = document.querySelectorAll('.filterable-item');
    
    items.forEach(function(item) {
        const text = item.textContent.toLowerCase();
        const matchesSearch = text.includes(searchTerm);
        
        // Apply filter select values
        let matchesFilters = true;
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(function(select) {
            const filterKey = select.dataset.filter;
            const filterValue = select.value;
            if (filterValue && item.dataset[filterKey] !== filterValue) {
                matchesFilters = false;
            }
        });
        
        item.style.display = (matchesSearch && matchesFilters) ? '' : 'none';
    });
}

/**
 * Course Add to Cart
 */
function addToCart(courseId, isMandatory = false) {
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            course_id: courseId,
            is_mandatory: isMandatory
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Ders sepete eklendi', 'success');
            updateCartCount(data.cart_count);
        } else {
            showNotification(data.message || 'Ders eklenemedi', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Bir hata oluştu', 'error');
    });
}

function removeFromCart(courseId) {
    fetch('/api/cart/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            course_id: courseId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Ders sepetten çıkarıldı', 'success');
            
            // Remove item from DOM
            const item = document.querySelector(`.cart-item[data-course-id="${courseId}"]`);
            if (item) {
                item.remove();
            }
            
            updateCartCount(data.cart_count);
            
            // Check if cart is empty
            const cartItems = document.querySelectorAll('.cart-item');
            if (cartItems.length === 0) {
                location.reload();
            }
        } else {
            showNotification(data.message || 'Ders çıkarılamadı', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Bir hata oluştu', 'error');
    });
}

function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-count');
    if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.style.display = count > 0 ? '' : 'none';
    }
}

/**
 * Toggle Mandatory Status
 */
function toggleMandatory(courseId, checkbox) {
    fetch('/api/cart/toggle-mandatory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            course_id: courseId,
            is_mandatory: checkbox.checked
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(checkbox.checked ? 'Zorunlu olarak işaretlendi' : 'Zorunlu işareti kaldırıldı', 'success');
        } else {
            checkbox.checked = !checkbox.checked;
            showNotification(data.message || 'İşlem başarısız', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        checkbox.checked = !checkbox.checked;
        showNotification('Bir hata oluştu', 'error');
    });
}

/**
 * Check Conflicts
 */
function checkConflicts() {
    const btn = document.querySelector('.check-conflicts-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Kontrol ediliyor...';
    }
    
    fetch('/api/cart/check-conflicts')
    .then(response => response.json())
    .then(data => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-clock"></i> Çakışma Kontrolü';
        }
        
        if (data.conflicts && data.conflicts.length > 0) {
            showConflictsModal(data.conflicts);
        } else {
            showNotification('Çakışma bulunamadı!', 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-clock"></i> Çakışma Kontrolü';
        }
        showNotification('Bir hata oluştu', 'error');
    });
}

function showConflictsModal(conflicts) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3><i class="fas fa-exclamation-triangle text-warning"></i> Çakışma Tespit Edildi</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                ${conflicts.map(conflict => `
                    <div class="conflict-item">
                        <strong>${conflict.course1.code}</strong> ile 
                        <strong>${conflict.course2.code}</strong> 
                        ${conflict.day} günü ${conflict.time} saatinde çakışıyor.
                    </div>
                `).join('')}
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Tamam</button>
            </div>
        </div>
    `;
    
    // Add styles
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1001;
    `;
    
    const modalContent = modal.querySelector('.modal');
    modalContent.style.cssText = `
        background: white;
        border-radius: 0.75rem;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow: auto;
    `;
    
    modal.querySelector('.modal-header').style.cssText = `
        padding: 1.25rem;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    `;
    
    modal.querySelector('.modal-body').style.cssText = `
        padding: 1.5rem;
    `;
    
    modal.querySelector('.modal-footer').style.cssText = `
        padding: 1rem 1.5rem;
        border-top: 1px solid #e2e8f0;
        text-align: right;
    `;
    
    modal.querySelectorAll('.conflict-item').forEach(item => {
        item.style.cssText = `
            padding: 0.75rem;
            background: #fef2f2;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            border-left: 4px solid #ef4444;
        `;
    });
    
    modal.querySelector('.modal-close').style.cssText = `
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        opacity: 0.5;
    `;
    
    document.body.appendChild(modal);
    
    // Close handlers
    modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

/**
 * Simulation
 */
function runSimulation() {
    const btn = document.querySelector('.run-simulation-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Simülasyon çalışıyor...';
    }
    
    fetch('/api/simulation/run', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Simülasyon tamamlandı!', 'success');
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } else {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Simülasyonu Başlat';
            }
            showNotification(data.message || 'Simülasyon başarısız', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-play"></i> Simülasyonu Başlat';
        }
        showNotification('Bir hata oluştu', 'error');
    });
}

/**
 * Format number with Turkish locale
 */
function formatNumber(num) {
    return new Intl.NumberFormat('tr-TR').format(num);
}

/**
 * Format percentage
 */
function formatPercentage(value) {
    return `%${value.toFixed(1)}`;
}
