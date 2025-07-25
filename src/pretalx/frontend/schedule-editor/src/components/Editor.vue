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

<script setup lang="ts">
import { computed } from 'vue'
import { getLocalizedString } from '../utils'

interface Speaker {
  name: string;
  code?: string;
}

interface Track {
  name: string | Record<string, string>;
}

interface Session {
  title: string | Record<string, string>;
  abstract?: string;
  speakers?: Speaker[];
  track?: Track;
  [key: string]: any;
}

defineProps<{
  session?: Session
}>()

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
