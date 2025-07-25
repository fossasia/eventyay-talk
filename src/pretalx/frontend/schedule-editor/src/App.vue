<template lang="pug">
.pretalx-schedule(:style="{'--scrollparent-width': scrollParentWidth + 'px'}", :class="draggedSession ? ['is-dragging'] : []", @pointerup="stopDragging")
	template(v-if="schedule")
		#main-wrapper
			#unassigned.no-print(v-scrollbar.y="", @pointerenter="isUnassigning = true", @pointerleave="isUnassigning = false")
				.title
					bunt-input#filter-input(v-model="unassignedFilterString", :placeholder="translations.filterSessions", icon="search")
					#unassigned-sort(@click="showUnassignedSortMenu = !showUnassignedSortMenu", :class="{'active': showUnassignedSortMenu}")
						i.fa.fa-sort
					#unassigned-sort-menu(v-if="showUnassignedSortMenu")
						.sort-method(v-for="method of unassignedSortMethods", @click="unassignedSort === method.name ? unassignedSortDirection = unassignedSortDirection * -1 : unassignedSort = method.name; showUnassignedSortMenu = false")
							span {{ method.label }}
							i.fa.fa-sort-amount-asc(v-if="unassignedSort === method.name && unassignedSortDirection === 1")
							i.fa.fa-sort-amount-desc(v-if="unassignedSort === method.name && unassignedSortDirection === -1")
				session.new-break(:session="{title: '+ ' + translations.newBreak}", :isDragged="false", @startDragging="startNewBreak", @click="showNewBreakHint", v-tooltip.fixed="{text: newBreakTooltip, show: newBreakTooltip}", @pointerleave="removeNewBreakHint")
				session(v-for="un in unscheduled", :key="un.id", :session="un", @startDragging="startDragging", :isDragged="draggedSession && un.id === draggedSession.id")
			#schedule-wrapper(v-scrollbar.x.y="")
				bunt-tabs.days(v-if="days", :modelValue="currentDay.format()", ref="tabs" :class="['grid-tabs']")
					bunt-tab(v-for="day of days", :key="day.format()", :id="day.format()", :header="day.format(dateFormat)", @selected="changeDay(day)")
				grid-schedule(:sessions="sessions",
					:rooms="schedule.rooms",
					:availabilities="availabilities",
					:warnings="warnings",
					:start="days[0]",
					:end="days.at(-1).clone().endOf('day')",
					:currentDay="currentDay",
					:draggedSession="draggedSession",
					@changeDay="currentDay = $event",
					@startDragging="startDragging",
					@rescheduleSession="rescheduleSession",
					@createSession="createSession",
					@editSession="editorStart($event)")
			#session-editor-wrapper(v-if="editorSession", @click="editorSession = null")
				form#session-editor(@click.stop="", @submit.prevent="editorSave")
					h3.session-editor-title(v-if="editorSession.code")
						a(v-if="editorSession.code", :href="`/orga/event/${eventSlug}/submissions/${editorSession.code}/`") {{editorSession.title }}
						span(v-else) {{editorSession.title }}
					.data
						.data-row(v-if="editorSession.code && editorSession.speakers && editorSession.speakers.length > 0").form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Speakers') }}
							.col-md-9.data-value
								span(v-for="speaker, index of editorSession.speakers")
									a(:href="`/orga/event/${eventSlug}/speakers/${speaker.code}/`") {{speaker.name}}
									span(v-if="index != editorSession.speakers.length - 1") {{', '}}
						.data-row(v-else).form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Title') }}
							.col-md-9
								.i18n-form-group
									template(v-for="locale of locales")
										input(v-model="editorSession.title[locale]", :required="true", :lang="locale", type="text")
						.data-row(v-if="editorSession.track").form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Track') }}
							.col-md-9.data-value {{ getLocalizedString(editorSession.track.name) }}
						.data-row(v-if="editorSession.room").form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Room') }}
							.col-md-9.data-value {{ getLocalizedString(editorSession.room.name) }}
						.data-row.form-control.form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Duration') }}
							.col-md-9.number.input-group
								input(v-model="editorSession.duration", type="number", min="1", max="1440", step="1", :required="true")
								.input-group-append
									span.input-group-text {{ $t('minutes') }}

						.data-row(v-if="editorSession.code && warnings[editorSession.code] && warnings[editorSession.code].length").form-group.row
							label.data-label.col-form-label.col-md-3
								i.fa.fa-exclamation-triangle.warning
								span {{ $t('Warnings') }}
							.col-md-9.data-value
								ul(v-if="warnings[editorSession.code].length > 1")
									li.warning(v-for="warning of warnings[editorSession.code]") {{ warning.message }}
								span(v-else) {{ warnings[editorSession.code][0].message }}
					.button-row
						input(type="submit")
						bunt-button#btn-delete(v-if="!editorSession.code", @click="editorDelete", :loading="editorSessionWaiting") {{ $t('Delete') }}
						bunt-button#btn-save(@click="editorSave", :loading="editorSessionWaiting") {{ $t('Save') }}
	bunt-progress-circular(v-else, size="huge", :page="true")
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, onBeforeMount, watch, nextTick } from 'vue'
import moment, { Moment } from 'moment-timezone'
import Editor from '~/components/Editor'
import GridSchedule from '~/components/GridSchedule'
import Session from '~/components/Session'
import api from '~/api'
import { getLocalizedString } from '~/utils'

interface Speaker {
  code: string;
  name: string;
}

interface Track {
  id: string;
  name: Record<string, string> | string;
}

interface Room {
  id: string;
  name: Record<string, string> | string;
}

interface Session {
  id?: string;
  code?: string;
  title: Record<string, string> | string;
  abstract?: string;
  speakers?: Speaker[] | string[];
  track?: string | Track;
  duration: number;
  state?: string;
  room?: string | Room;
  start?: string | Moment;
  end?: string | Moment;
  uncreated?: boolean;
  updated?: string;
  availabilities?: any;
}

interface Schedule {
  event_start: string;
  event_end: string;
  timezone: string;
  locales: string[];
  rooms: Room[];
  tracks: Track[];
  speakers: Speaker[];
  talks: Session[];
  version: string;
  now?: string; // Added now property
}

interface Availability {
  start: string;
  end: string;
}

interface Warning {
  message: string;
}

interface Availabilities {
  rooms: Record<string, Availability[]>;
  talks: Record<string, Availability[]>;
}

const props = defineProps({
  locale: String,
  version: {
    type: String,
    default: ''
  }
})

const eventSlug = ref<string | null>(null)
const scrollParentWidth = ref<number>(Infinity)
const schedule = ref<Schedule | null>(null)
const availabilities = reactive<Availabilities>({ rooms: {}, talks: {} })
const warnings = reactive<Record<string, Warning[]>>({})
const currentDay = ref<Moment | null>(null)
const draggedSession = ref<Session | null>(null)
const editorSession = ref<Session | null>(null)
const editorSessionWaiting = ref<boolean>(false)
const isUnassigning = ref<boolean>(false)
const locales = ref<string[]>(["en"])
const unassignedFilterString = ref<string>('')
const unassignedSort = ref<string>('title')
const unassignedSortDirection = ref<number>(1)
const showUnassignedSortMenu = ref<boolean>(false)
const newBreakTooltip = ref<string>('')
const translations = reactive({
  filterSessions: $t('Filter sessions'),
  newBreak: $t('New break'),
})
const eventTimezone = ref<string | null>(null)
const since = ref<string | undefined>()

function $t(key: string): string {
  return (typeof window !== 'undefined' && (window as any).$t) ? 
    (window as any).$t(key) : key;
}

const roomsLookup = computed(() => {
  if (!schedule.value) return {}
  return schedule.value.rooms.reduce((acc: Record<string, Room>, room) => {
    acc[room.id] = room
    return acc
  }, {})
})

const tracksLookup = computed(() => {
  if (!schedule.value) return {}
  return schedule.value.tracks.reduce((acc: Record<string, Track>, t) => {
    acc[t.id] = t
    return acc
  }, {})
})

const speakersLookup = computed(() => {
  if (!schedule.value) return {}
  return schedule.value.speakers.reduce((acc: Record<string, Speaker>, s) => {
    acc[s.code] = s
    return acc
  }, {})
})

const unassignedSortMethods = computed(() => {
  const sortMethods = [
    { label: $t('Title'), name: 'title' },
    { label: $t('Speakers'), name: 'speakers' },
  ]
  if (schedule.value && schedule.value.tracks.length > 1) {
    sortMethods.push({ label: $t('Track'), name: 'track' })
  }
  sortMethods.push({ label: $t('Duration'), name: 'duration' })
  return sortMethods
})

const unscheduled = computed(() => {
  if (!schedule.value) return []
  let sessions: Session[] = []
  for (const session of schedule.value.talks.filter(s => !s.start || !s.room)) {
    sessions.push({
      id: session.id,
      code: session.code,
      title: session.title,
      abstract: session.abstract,
      speakers: session.speakers?.map(s => speakersLookup.value[s as string]),
      track: tracksLookup.value[session.track as string],
      duration: session.duration,
      state: session.state,
    })
  }
  if (unassignedFilterString.value.length) {
    sessions = sessions.filter(s => {
      const title = getLocalizedString(s.title)
      const speakers = (s.speakers as Speaker[])?.map(s => s.name).join(', ') || ''
      return title.toLowerCase().includes(unassignedFilterString.value.toLowerCase()) || 
             speakers.toLowerCase().includes(unassignedFilterString.value.toLowerCase())
    })
  }
  sessions = sessions.sort((a, b) => {
    if (unassignedSort.value == 'title') {
      return getLocalizedString(a.title).toUpperCase().localeCompare(
        getLocalizedString(b.title).toUpperCase()
      ) * unassignedSortDirection.value
    } else if (unassignedSort.value == 'speakers') {
      const aSpeakers = (a.speakers as Speaker[])?.map(s => s.name).join(', ') || ''
      const bSpeakers = (b.speakers as Speaker[])?.map(s => s.name).join(', ') || ''
      return aSpeakers.toUpperCase().localeCompare(bSpeakers.toUpperCase()) * unassignedSortDirection.value
    } else if (unassignedSort.value == 'track') {
      return getLocalizedString((a.track as Track)?.name || '').toUpperCase().localeCompare(
        getLocalizedString((b.track as Track)?.name || '').toUpperCase()
      ) * unassignedSortDirection.value
    } else if (unassignedSort.value == 'duration') {
      return (a.duration - b.duration) * unassignedSortDirection.value
    }
    return 0
  })
  return sessions
})

const sessions = computed(() => {
  if (!schedule.value) return []
  const sessions: Session[] = []
  for (const session of schedule.value.talks.filter(
    s => s.start && moment(s.start).isSameOrAfter(days.value[0]) && 
    moment(s.start).isSameOrBefore(days.value.at(-1)!.clone().endOf('day')))) {
    sessions.push({
      id: session.id,
      code: session.code,
      title: session.title,
      abstract: session.abstract,
      start: moment(session.start as string),
      end: moment(session.end as string),
      duration: moment(session.end as string).diff(session.start, 'm'),
      speakers: session.speakers?.map(s => speakersLookup.value[s as string]),
      track: tracksLookup.value[session.track as string],
      state: session.state,
      room: roomsLookup.value[session.room as string]
    })
  }
  sessions.sort((a, b) => (a.start as Moment).diff(b.start as Moment))
  return sessions
})

const days = computed((): Moment[] => {
  if (!schedule.value) return []
  const days = [moment(schedule.value.event_start).startOf('day')]
  const lastDay = moment(schedule.value.event_end)
  while (!days.at(-1)!.isSame(lastDay, 'day')) {
    days.push(days.at(-1)!.clone().add(1, 'days'))
  }
  return days
})

const dateFormat = computed(() => {
  if ((schedule.value && schedule.value.rooms.length > 2) || !days.value || !days.value.length) return 'dddd DD. MMMM'
  if (days.value && days.value.length <= 5) return 'dddd DD. MMMM'
  if (days.value && days.value.length <= 7) return 'dddd DD. MMM'
  return 'ddd DD. MMM'
})

const userTimezone = ref<string>(moment.tz.guess())

async function fetchSchedule(options?: { since?: string; warnings?: boolean }): Promise<Schedule> {
  const sched = await api.fetchTalks(options)
  return sched
}

async function fetchAdditionalScheduleData() {
  Object.assign(availabilities, await api.fetchAvailabilities())
  Object.assign(warnings, await api.fetchWarnings())
}

function changeDay(day: Moment) {
  if (currentDay.value && day.isSame(currentDay.value)) return
  currentDay.value = moment(day).startOf('day')
  window.location.hash = day.format('YYYY-MM-DD')
}

function saveTalk(session: Session) {
  // Convert to API-compatible format
  const talkData = {
    id: session.id,
    code: session.code,
    title: session.title,
    description: session.abstract,
    room: session.room,
    start: typeof session.start === 'object' ? session.start.format() : session.start,
    end: typeof session.end === 'object' ? session.end.format() : session.end,
    duration: session.duration
  }
  
  api.saveTalk(talkData).then((response: any) => {
    if (session.code && response?.warnings) {
      warnings[session.code] = response.warnings
    }
    const foundSession = schedule.value?.talks.find(s => s.id === session.id)
    if (foundSession) {
      foundSession.updated = response?.updated
    }
  })
}

function rescheduleSession(e: any) {
  if (!schedule.value) return
  const movedSession = schedule.value.talks.find(s => s.id === e.session.id)
  if (!movedSession) return
  stopDragging()
  
  // Set to string values for API compatibility
  movedSession.start = e.start
  movedSession.end = e.end
  movedSession.room = e.room.id
  
  saveTalk(movedSession)
}

function createSession(e: any) {
  api.createTalk({
    ...e.session,
    start: e.session.start.format(),
    end: e.session.end.format(),
    room: e.room.id
  }).then((response: any) => {
    if (e.session.code && response?.warnings) {
      warnings[e.session.code] = response.warnings
    }
    const newSession = { 
      ...e.session,
      id: response.id,
      start: moment(e.session.start),
      end: moment(e.session.end),
      room: roomsLookup.value[e.room.id]
    }
    schedule.value?.talks.push(newSession)
    editorStart(newSession)
  })
}

function editorStart(session: Session) {
  editorSession.value = session
}

function editorSave() {
  if (!editorSession.value) return
  editorSessionWaiting.value = true
  
  // Handle moment conversion
  if (typeof editorSession.value.start === 'object') {
    editorSession.value.end = moment(editorSession.value.start).clone()
      .add(editorSession.value.duration, 'm')
  }
  
  saveTalk(editorSession.value)
  const session = schedule.value?.talks.find(s => s.id === editorSession.value?.id)
  if (session) {
    session.end = editorSession.value.end
    if (!(session as any).submission) {
      session.title = editorSession.value.title
    }
  }
  editorSessionWaiting.value = false
  editorSession.value = null
}

function editorDelete() {
  if (!editorSession.value) return
  editorSessionWaiting.value = true
  api.deleteTalk({ id: editorSession.value.id! })
  if (schedule.value) {
    schedule.value.talks = schedule.value.talks.filter(s => s.id !== editorSession.value?.id)
  }
  editorSessionWaiting.value = false
  editorSession.value = null
}

function showNewBreakHint() {
  newBreakTooltip.value = $t('Drag the box to the schedule to create a new break')
}

function removeNewBreakHint() {
  newBreakTooltip.value = ''
}

function startNewBreak({ event }: { event: Event }) {
  const title = locales.value.reduce((obj, locale) => {
    (obj as Record<string, string>)[locale] = $t('New break')
    return obj
  }, {})
  startDragging({ event, session: { 
    title, 
    duration: 5, 
    uncreated: true,
    id: 'temp-' + Date.now()  // Temporary ID
  } })
}

function startDragging({ event, session }: { event: Event; session: Session }) {
  if (session.id && availabilities.talks[session.id]) {
    session.availabilities = availabilities.talks[session.id]
  }
  draggedSession.value = session
}

function stopDragging() {
  try {
    if (isUnassigning.value && draggedSession.value && schedule.value) {
      if (draggedSession.value.code) {
        const movedSession = schedule.value.talks.find(s => s.id === draggedSession.value?.id)
        if (movedSession) {
          movedSession.start = undefined
          movedSession.end = undefined
          movedSession.room = undefined
          saveTalk(movedSession)
        }
      } else if (draggedSession.value.id && schedule.value.talks.find(s => s.id === draggedSession.value?.id)) {
        schedule.value.talks = schedule.value.talks.filter(s => s.id !== draggedSession.value?.id)
        if (draggedSession.value.id) {
          api.deleteTalk({ id: draggedSession.value.id })
        }
      }
    }
  } finally {
    draggedSession.value = null
    isUnassigning.value = false
  }
}

function onWindowResize() {
  scrollParentWidth.value = document.body.offsetWidth
}

async function pollUpdates() {
  if (!schedule.value) return
  
  fetchSchedule({ since: since.value, warnings: true }).then(sched => {
    if (sched.version !== schedule.value?.version) {
      window.location.reload()
    }
    sched.talks.forEach((talk: Session) => {
      const oldTalk = schedule.value?.talks.find(t => t.id === talk.id)
      if (!oldTalk) {
        schedule.value?.talks.push(talk)
      } else if (talk.updated && oldTalk.updated) {
        if (moment(talk.updated).isAfter(moment(oldTalk.updated))) {
          Object.assign(oldTalk, talk)
        }
      }
    })
    // Handle 'now' property safely
    if ('now' in sched) {
      since.value = sched.now
    }
    window.setTimeout(pollUpdates, 10 * 1000)
  })
}

onBeforeMount(async () => {
  schedule.value = await fetchSchedule()
  if (schedule.value) {
    eventTimezone.value = schedule.value.timezone
    moment.tz.setDefault(eventTimezone.value)
    locales.value = schedule.value.locales
    if (days.value.length) {
      currentDay.value = days.value[0]
    }
  }
  eventSlug.value = window.location.pathname.split("/")[3]
  window.setTimeout(pollUpdates, 10 * 1000)
  await fetchAdditionalScheduleData()
  await new Promise<void>((resolve) => {
    const poll = () => {
      const el = document.querySelector('.pretalx-schedule')
      if (el && (el.parentElement || (el as any).getRootNode().host)) return resolve()
      setTimeout(poll, 100)
    }
    poll()
  })
})

onMounted(() => {
  window.addEventListener('resize', onWindowResize)
  onWindowResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
})
</script>

<style lang="stylus">
#page-content
	padding: 0
.pretalx-schedule
	display: flex
	flex-direction: column
	min-height: 0
	min-width: 0
	height: calc(100vh - 160px)
	width: 100%
	font-size: 14px
	margin-left: 24px
	font-family: var(--font-family)
	color: var(--color-text)
	h1, h2, h3, h4, h5, h6, legend, button, .btn
		font-family: var(--font-family-title)
	&.is-dragging
		user-select: none
		cursor: grabbing
	#main-wrapper
		display: flex
		flex: auto
		min-height: 0
		min-width: 0
	.settings
		margin-left: 18px
		align-self: flex-start
		display: flex
		align-items: center
		position: sticky
		z-index: 100
		left: 18px
		.bunt-select
			max-width: 300px
			padding-right: 8px
		.timezone-label
			cursor: default
			color: $clr-secondary-text-light
	.days
		background-color: $clr-white
		tabs-style(active-color: var(--color-primary), indicator-color: var(--color-primary), background-color: transparent)
		overflow-x: auto
		position: sticky
		left: 0
		top: 0
		margin-bottom: 0
		flex: none
		min-width: 0
		height: 48px
		z-index: 30
		.bunt-tabs-header
			min-width: min-content
		.bunt-tabs-header-items
			justify-content: center
			min-width: min-content
			.bunt-tab-header-item
				min-width: min-content
			.bunt-tab-header-item-text
				white-space: nowrap
	#unassigned
		margin-top: 35px
		width: 350px
		flex: none
		> *
			margin-right: 12px
		> .bunt-scrollbar-rail-y
			margin: 0
		> .title
			padding 4px 0
			font-size: 18px
			text-align: center
			background-color: $clr-white
			border-bottom: 4px solid $clr-dividers-light
			display: flex
			align-items: flex-end
			margin-left: 8px
			#filter-input
				width: calc(100% - 36px)
				.label-input-container, .label-input-container:active
					.outline
						display: none
			#unassigned-sort
				width: 28px
				height: 28px
				text-align: center
				cursor: pointer
				border-radius: 4px
				margin-bottom: 8px
				margin-left: 4px
				color: $clr-secondary-text-light
				&:hover, &.active
					opacity: 0.8
					background-color: $clr-dividers-light
		.new-break.c-linear-schedule-session
			min-height: 48px
		#unassigned-sort-menu
			color: $clr-primary-text-light
			display: flex
			flex-direction: column
			background-color: white
			position: absolute
			top: 53px
			right: 15px
			width: 130px
			font-size: 16px
			cursor: pointer
			z-index: 1000
			box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5)
			text-align: left;
			.sort-method
				padding: 8px 16px
				display: flex
				justify-content: space-between
				align-items: center
				&:hover
					background-color: $clr-dividers-light
	#schedule-wrapper
		width: 100%
		margin-right: 40px
  #session-editor-wrapper
		position: absolute
		z-index: 1000
		top: 0
		left: 0
		width: 100%
		height: 100%
		background-color: rgba(0, 0, 0, 0.5)

		#session-editor
			background-color: $clr-white
			border-radius: 4px
			padding: 32px 40px
			position: absolute
			top: 50%
			left: 50%
			transform: translate(-50%, -50%)
			width: 680px

			.session-editor-title
				font-size: 22px
				margin-bottom: 16px
			.button-row
				display: flex
				width: 100%
				margin-top: 24px

				.bunt-button-content
					font-size: 16px !important
				#btn-delete
					button-style(color: $clr-danger, text-color: $clr-white)
					font-weight: bold;
				#btn-save
					margin-left: auto
					font-weight: bold;
					button-style(color: #2185d0)
				[type=submit]
					display: none
			.data
				display: flex
				flex-direction: column
				font-size: 16px
				.data-row
					.data-value
						padding-top: 8px
						ul
							list-style: none
							padding: 0
		.warning
			color: #b23e65
</style>
