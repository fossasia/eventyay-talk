<script setup lang="ts">
import { ref } from 'vue'

const ENTRY_CLASSES = 'text-gray-700 hover:bg-gray-100 p-2'
const open = ref(false)

function showMenu() {
  open.value = true
  console.log('showMenu')
}

function closeMenu() {
  open.value = false
  console.log('closeMenu')
}
</script>

<template>
  <div class='relative'>
    <h1 class='text-xl cursor-pointer' @mouseenter='showMenu'>User name</h1>
    <ul v-if='open' class='absolute bg-white border border-gray-300 rounded shadow-lg p-4 top-4 cursor-pointer list-none'>
      <li :class='ENTRY_CLASSES'>One</li>
      <li :class='ENTRY_CLASSES'>Two</li>
      <li :class='ENTRY_CLASSES'>Three</li>
    </ul>
  </div>
</template>

<style scoped>
</style>
