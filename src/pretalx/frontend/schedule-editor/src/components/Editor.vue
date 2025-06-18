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

<script>
import { defineComponent } from 'vue'
import { getLocalizedString } from '../utils'

export default defineComponent({
	name: 'Editor',
	props: {
		session: {
			type: Object,
			default: null
		}
	},
	computed: {
		something() {
			return true
		}
	},
	created() {},
	mounted() {},
	methods: {
		getLocalizedString,
		somethingMethod(foo) {
			return foo
		}
	}
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
