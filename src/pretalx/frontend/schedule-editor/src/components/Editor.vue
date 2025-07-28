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

<script lang="ts" setup>
import { computed, defineProps } from 'vue'
import { getLocalizedString } from '../utils'

interface Speaker {
  name: string
  code?: string
}

interface Track {
  name: string | Record<string, string>
}

interface Session {
  title: string | Record<string, string>
  speakers?: Speaker[]
  abstract?: string
  track?: Track
  [key: string]: any
}

const props = defineProps<{
  session: Session | null
}>()

const something = computed(() => true)

function somethingMethod(foo: any): any {
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
