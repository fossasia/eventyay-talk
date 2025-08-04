(function() {
    'use strict';
    
    function initDropdowns() {
        // Handle click outside to close dropdowns
        document.addEventListener('click', function(event) {
            const openDropdowns = document.querySelectorAll('details.dropdown[open]');
            
            openDropdowns.forEach(function(dropdown) {
                if (!dropdown.contains(event.target)) {
                    dropdown.removeAttribute('open');
                }
            });
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDropdowns);
    } else {
        initDropdowns();
    }
})();
