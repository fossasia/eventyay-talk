// Dropdown manu to navigate to other Eventyay components.

document.addEventListener('alpine:init', () => {
  Alpine.data('global-nav', () => ({
    open: false,

    openMenu() {
      this.open = true
    },

    closeMenu() {
      this.open = false
    }
  }))
})
