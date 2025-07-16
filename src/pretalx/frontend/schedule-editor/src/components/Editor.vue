<template lang="pug">
.schedule-editor#editor
	template(v-if="session")
		h1 {{ session.title }}
		.speakers(v-if="session.speakers") {{ session.speakers.map(s => s.name).join(', ') }}
		template(v-if="session.abstract")
			hr
			.abstract {{ session.abstract }}
			.track(v-if="session.track") {{ getLocalizedString(session.track.name) }}
		.session {{ session }}
</template>

<script setup>
import { defineComponent, computed } from 'vue'
import { getLocalizedString } from '../utils'

const props = defineProps({
	session: {
		type: Object,
		default: null
	}
})

const something = computed(() => true)

function somethingMethod(foo) {
	return foo
}

defineOptions({
	name: 'Editor'
})
</script>

<style lang="stylus">
#editor
	display: none
	card()
	flex: none
	width: 400px
	padding-left: 32px
	/* todo: box-shadow/border */
</style>
