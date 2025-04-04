<script setup lang="ts">
import { ref, useTemplateRef, onMounted, onBeforeUnmount } from 'vue'

const ENTRY_CLASSES = ' text-gray-700 hover:bg-gray-100 p-2 block no-underline hover:underline'
const open = ref(false)
const subOpen = ref(false)
const container = useTemplateRef('container')

function showMenu() {
  open.value = true
  console.log('showMenu')
}

function closeMenu() {
  open.value = false
  console.log('closeMenu')
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (container.value && !container.value.contains(target)) {
    closeMenu()
  }
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div class='relative' ref='container'>
    <button class='text-xl cursor-pointer' @click='showMenu'>User name</button>
    <div v-if='open' ref='main-menu' class='absolute z-1 end-1 grid grid-cols-1 shadow shadow-lg min-w-32'>
      <div class='relative cursor-pointer' @mouseover='subOpen = true' @mouseleave='subOpen = false'>
        <div :class='ENTRY_CLASSES' >
          Dashboard
        </div>
        <ul v-if='subOpen' class='absolute z-2 top-0 -translate-x-full list-none m-0 p-s-0 bg-white shadow-lg min-w-36'>
          <li>
            <a href='/common/' :class='ENTRY_CLASSES' class='block'>Main dashboard</a>
          </li>
          <li>
            <a href='/tickets/control/' :class='ENTRY_CLASSES' class='block'>Tickets</a>
          </li>
          <li>
            <a href='/talk/orga/event/' :class='ENTRY_CLASSES' class='block'>Talks</a>
          </li>
        </ul>
      </div>
      <a :class='ENTRY_CLASSES' href='/tickets/common/events/'>My events</a>
      <a :class='ENTRY_CLASSES' href='/tickets/common/organizers/'>Organizers</a>
      <a class='border-t border-s-0 border-e-0 border-b-0 border-solid border-gray-300' :class='ENTRY_CLASSES' href='/tickets/common/account/'>Accounts</a>
      <a class='border-t border-s-0 border-e-0 border-b-0 border-solid border-gray-300' :class='ENTRY_CLASSES' href='/tickets/control/admin/'>Admin</a>
      <a class='border-t border-s-0 border-e-0 border-b-0 border-solid border-gray-300' :class='ENTRY_CLASSES' href='/tickets/control/logout'>Logout</a>
    </div>
  </div>
</template>

<style scoped>
</style>
