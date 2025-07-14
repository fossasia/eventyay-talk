<template lang="pug">
.c-grid-schedule(ref="rootRef")
	.grid(ref="gridRef", :style="gridStyle", :class="gridClasses", @pointermove="updateHoverSlice($event)", @pointerup="stopDragging($event)")
		template(v-for="slice of visibleTimeslices", :key="slice.name")
			.timeslice(:ref="el => setSliceRef(el, slice.name)", :class="getSliceClasses(slice)", :data-slice="slice.date.format()", :style="getSliceStyle(slice)", @click="expandTimeslice(slice)") {{ getSliceLabel(slice) }}
				svg(viewBox="0 0 10 10", v-if="isSliceExpandable(slice)").expand
					path(d="M 0 4 L 5 0 L 10 4 z")
					path(d="M 0 6 L 5 10 L 10 6 z")
			.timeseparator(:class="getSliceClasses(slice)", :style="getSliceStyle(slice)")
		.room(:style="{'grid-area': `1 / 1 / auto / auto`}")
		.room(v-for="(room, i) of visibleRooms", :key="room.id", :style="{'grid-area': `1 / ${i + 2} / auto / auto`}")
			span {{ getLocalizedString(room.name) }}
			.hide-room.no-print(v-if="visibleRooms.length > 1", @click="hiddenRooms = rooms.filter(r => hiddenRooms.includes(r) || r === room)")
				i.fa.fa-eye-slash
		session(v-if="draggedSession && hoverSlice", :style="getHoverSliceStyle()", :session="draggedSession", :isDragClone="true", :overrideStart="hoverSlice.time")
		template(v-for="session of visibleSessions", :key="session.id")
			session(
				:session="session",
				:warnings="session.code ? warnings[session.code] : []",
				:isDragged="draggedSession && (session.id === draggedSession.id)",
				:style="getSessionStyle(session)",
				:showRoom="false",
				@startDragging="startDragging($event)",
			)
		.availability(v-for="availability of visibleAvailabilities", :key="`${availability.room.id}-${availability.start.valueOf()}-${availability.end.valueOf()}`", :style="getSessionStyle(availability)", :class="availability.active ? ['active'] : []")
	#hiddenRooms.no-print(v-if="hiddenRooms.length")
		h4 {{ $t('Hidden rooms') }} ({{ hiddenRooms.length }})
		.room-list
			.room-entry(v-for="room of hiddenRooms", :key="room.id", @click="hiddenRooms.splice(hiddenRooms.indexOf(room), 1)")
				.span {{ getLocalizedString(room.name) }}
				.show-room(@click.stop="hiddenRooms.splice(hiddenRooms.indexOf(room), 1)")
					i.fa.fa-eye
</template>

<script>
import { defineComponent, ref, computed, watch, onMounted, onUnmounted, nextTick, inject } from 'vue'
import moment from 'moment-timezone'
import Session from './Session'
import { getLocalizedString } from '~/utils'

const getSliceName = function (date) {
	return `slice-${date.format('MM-DD-HH-mm')}`
}

export default defineComponent({
	name: 'GridSchedule',
	components: { Session },
	props: {
		sessions: {
			type: Array,
			default: () => []
		},
		availabilities: {
			type: Object,
			default: () => ({})
		},
		warnings: {
			type: Object,
			default: () => ({})
		},
		start: {
			type: Object,
			required: true
		},
		end: {
			type: Object,
			required: true
		},
		rooms: {
			type: Array,
			default: () => []
		},
		currentDay: {
			type: Object,
			default: null
		},
		draggedSession: {
			type: Object,
			default: null
		}
	},
	setup(props, { emit }) {
		// Injections
		const eventUrl = inject('eventUrl', null)
		const generateSessionLinkUrl = inject('generateSessionLinkUrl', ({eventUrl, session}) => `${eventUrl}talk/${session.id}/`)

		// Refs
		const rootRef = ref(null)
		const gridRef = ref(null)
		const sliceRefs = ref({})  // Object to store slice references
		const observer = ref(null)
		
		const scrolledDay = ref(null)
		const hoverSlice = ref(null)
		const expandedTimes = ref([])
		const gridOffset = ref(0)
		const dragScrollTimer = ref(null)
		const dragStart = ref(null)
		const hiddenRooms = ref([])
		
		// Store timeslice references
		const setSliceRef = (el, name) => {
			if (el) {
				sliceRefs.value[name] = el
			}
		}
		
		// Computed properties
		const hoverSliceLegal = computed(() => {
			if (!hoverSlice.value || !hoverSlice.value.room) return false
			const start = hoverSlice.value.time
			const end = hoverSlice.value.time.clone().add(props.draggedSession.duration, 'm')
			const sessionId = props.draggedSession.id
			const roomId = hoverSlice.value.room.id
			
			for (const session of props.sessions.filter(s => s.start)) {
				if (session.room.id === roomId && session.id !== sessionId) {
					// Test all same-room sessions for overlap with our new session:
					// Overlap exists if this session's start or end falls within our session
					if (session.start.isSame(start) || session.end.isSame(end)) return false
					if (session.start.isBetween(start, end) || session.end.isBetween(start, end)) return false
					// or the other way around (to take care of either session containing the other completely)
					if (start.isBetween(session.start, session.end) || end.isBetween(session.start, session.end)) return false
				}
			}
			return true
		})
		
		const hoverEndSlice = computed(() => {
			if (props.draggedSession && hoverSlice.value) {
				return hoverSlice.value.time.clone().add(props.draggedSession.duration, 'm')
			}
			return null
		})
		
		const timeslices = computed(() => {
			const minimumSliceMins = 30
			const slices = []
			const slicesLookup = {}
			const pushSlice = function (date, {hasStart = false, hasEnd = false, hasSession = false, isExpanded = false} = {}) {
				const name = getSliceName(date)
				let slice = slicesLookup[name]
				if (slice) {
					slice.hasSession = slice.hasSession || hasSession
					slice.hasStart = slice.hasStart || hasStart
					slice.hasEnd = slice.hasEnd || hasEnd
					slice.isExpanded = slice.isExpanded || isExpanded
				} else {
					slice = {
						date,
						name,
						hasSession,
						hasStart,
						hasEnd,
						isExpanded,
						datebreak: date.isSame(date.clone().startOf('day'))
					}
					slices.push(slice)
					slicesLookup[name] = slice
				}
			}
			const fillHalfHours = function (start, end, {hasSession} = {}) {
				// fill to the nearest half hour, then each half hour, then fill to end
				let mins = end.diff(start, 'minutes')
				const startingMins = minimumSliceMins - start.minute() % minimumSliceMins
				// buffer slices because we need to remove hasSession from the last one
				const halfHourSlices = []
				if (startingMins) {
					halfHourSlices.push(start.clone().add(startingMins, 'minutes'))
					mins -= startingMins
				}
				const endingMins = end.minute() % minimumSliceMins
				for (let i = 1; i <= mins / minimumSliceMins; i++) {
					halfHourSlices.push(start.clone().add(startingMins + minimumSliceMins * i, 'minutes'))
				}

				if (endingMins) {
					halfHourSlices.push(end.clone().subtract(endingMins, 'minutes'))
				}

				// last slice is actually just after the end of the session and has no session
				const lastSlice = halfHourSlices.pop()
				halfHourSlices.forEach(slice => pushSlice(slice, {hasSession}))
				pushSlice(lastSlice)
			}
			for (const session of props.sessions) {
				const lastSlice = slices[slices.length - 1]
				// gap to last slice
				if (!lastSlice) {
					pushSlice(session.start.clone().startOf('day'))
				} else if (session.start.isAfter(lastSlice.date, 'minutes')) {
					fillHalfHours(lastSlice.date, session.start)
				}

				// add start and end slices for the session itself
				pushSlice(session.start, {hasStart: true, hasSession: true})
				pushSlice(session.end, {hasEnd: true})
				// add half hour slices between a session
				fillHalfHours(session.start, session.end, {hasSession: true})
			}
			
			// Add expanded times
			expandedTimes.value.forEach(time => {
				pushSlice(time, {isExpanded: true})
			})
			
			// Always show business hours
			fillHalfHours(props.start, props.end)
			
			if (hoverEndSlice.value) {
				pushSlice(hoverEndSlice.value, {hasEnd: true})
			}
			
			const sliceIsFraction = function (slice) {
				if (!slice) return false
				return slice.date.minutes() !== 0 && slice.date.minutes() !== minimumSliceMins
			}
			const sliceShouldDisplay = function (slice, index) {
				if (!slice) return false
				// keep slices with sessions or when changing dates, or when sessions start or immediately after they end
				if (slice.hasSession || slice.datebreak || slice.hasStart || slice.hasEnd || slice.isExpanded) return true
				// keep slices between 9 and 18 o'clock
				if (slice.date.hour() >= 9 && slice.date.hour() < 19) return true
				const prevSlice = slices[index - 1]
				const nextSlice = slices[index + 1]

				// keep non-whole slices
				if (sliceIsFraction(slice)) return true
				// keep slices before and after non-whole slices, if by session or break
				if (
					((prevSlice?.hasSession || prevSlice?.hasBreak || prevSlice?.hasEnd) && sliceIsFraction(prevSlice)) ||
					((nextSlice?.hasSession || nextSlice?.hasBreak) && sliceIsFraction(nextSlice)) ||
					((!nextSlice?.hasSession || !nextSlice?.hasBreak) && (slice.hasSession || slice.hasBreak) && sliceIsFraction(nextSlice))
				) return true
				// but drop slices inside breaks
				if (prevSlice?.hasBreak && slice.hasBreak) return false
				return false
			}
			slices.sort((a, b) => a.date.diff(b.date))
			const compactedSlices = []
			for (const [index, slice] of slices.entries()) {
				if (sliceShouldDisplay(slice, index)) {
					compactedSlices.push(slice)
					continue
				}
				// make the previous slice a gap slice if this one would be the first to be removed
				// but only if it isn't the start of the day
				const prevSlice = slices[index - 1]
				if (prevSlice && sliceShouldDisplay(prevSlice, index - 1) && !prevSlice.datebreak) {
					prevSlice.gap = true
				}
			}
			return compactedSlices
		})
		
		const oddTimeslices = computed(() => {
			const result = new Set()
			props.sessions.forEach(session => {
				if (session.start.minute() % 30 !== 0) result.add(session.start.valueOf())
				if (session.end.minute() % 30 !== 0) result.add(session.end.valueOf())
			})
			return Array.from(result).map(t => moment(t))
		})
		
		const visibleTimeslices = computed(() => {
		  return timeslices.value.filter(slice => {
			  // Compare using timestamps instead of object references
			  const isExpanded = expandedTimes.value.some(t => t.isSame(slice.date))
			  const isOdd = oddTimeslices.value.some(t => t.isSame(slice.date))
			  
			  return slice.date.minute() % 30 === 0 || isExpanded || isOdd
		  })
		})
		
		const gridStyle = computed(() => {
			let rows = '[header] 52px '
			rows += timeslices.value.map((slice, index) => {
				const next = timeslices.value[index + 1]
				let height = 60
				if (slice.gap) {
					height = 100
				} else if (slice.datebreak) {
					height = 60
				} else if (next) {
					height = Math.min(60, next.date.diff(slice.date, 'minutes') * 2)
				}
				return `[${slice.name}] minmax(${height}px, auto)`
			}).join(' ')
			return {
				'--total-rooms': visibleRooms.value.length,
				'grid-template-rows': rows
			}
		})
		
		const gridClasses = computed(() => {
			const result = []
			if (props.draggedSession) result.push('is-dragging')
			if (hoverSlice.value && props.draggedSession && !hoverSliceLegal.value) result.push('illegal-hover')
			return result
		})
		
		const availabilitySlices = computed(() => {
			const avails = []
			if (!visibleTimeslices.value?.length) return avails
			const earliestStart = visibleTimeslices.value[0].date
			const latestEnd = visibleTimeslices.value.at(-1).date
			const draggedAvails = []
			
			if (props.draggedSession && props.availabilities.talks?.[props.draggedSession.id]?.length) {
				for (const avail of props.availabilities.talks[props.draggedSession.id]) {
					draggedAvails.push({
						start: moment(avail.start),
						end: moment(avail.end),
					})
				}
			}
			
			for (const room of visibleRooms.value) {
				if (!props.availabilities.rooms?.[room.id] || !props.availabilities.rooms[room.id].length) {
					avails.push({room: room, start: earliestStart, end: latestEnd})
				} else {
					for (const avail of props.availabilities.rooms[room.id]) {
						avails.push({
							room: room,
							start: moment(avail.start),
							end: moment(avail.end)
						})
					}
				}
				for (const avail of draggedAvails) {
					avails.push({
						room: room,
						start: avail.start,
						end: avail.end,
						active: true
					})
				}
			}
			return avails
		})
		
		const staticOffsetTop = computed(() => {
			if (!rootRef.value?.parentElement) return 0
			const rect = rootRef.value.parentElement.getBoundingClientRect()
			return rect.top
		})
		
		const scrollParent = computed(() => {
			return rootRef.value?.parentElement
		})
		
		const visibleRooms = computed(() => {
			return props.rooms.filter(room => !hiddenRooms.value.includes(room))
		})
		
		const visibleSessions = computed(() => {
			return props.sessions.filter(session => !hiddenRooms.value.includes(session.room))
		})
		
		const visibleAvailabilities = computed(() => {
			const result = []
			for (const avail of availabilitySlices.value) {
				if (hiddenRooms.value.includes(avail.room)) continue
				const start = visibleTimeslices.value.find(slice => slice.date.isSameOrAfter(avail.start))
				const end = visibleTimeslices.value.find(slice => slice.date.isSameOrAfter(avail.end))
				if (!start || !end) continue
				result.push({
					room: avail.room,
					start: start.date,
					end: end.date,
					active: avail.active
				})
			}
			return result
		})
		
		// Methods
		const startDragging = ({session, event}) => {
			dragStart.value = {
				x: event.clientX,
				y: event.clientY,
				session: session,
				now: moment(),
			}
			emit('startDragging', {event, session})
		}
		
		const stopDragging = (event) => {
			if (dragStart.value && props.draggedSession) {
				const distance = dragStart.value.x - event.clientX + dragStart.value.y - event.clientY
				const timeDiff = moment().diff(dragStart.value.now, 'ms')
				const session = dragStart.value.session
				dragStart.value = null
				if (distance < 5 && distance > -5 && timeDiff < 500) {
					emit('editSession', session)
					return
				}
			}
			if (!props.draggedSession || !hoverSlice.value || !hoverSliceLegal.value) return
			const start = hoverSlice.value.time
			const end = hoverSlice.value.time.clone().add(props.draggedSession.duration, 'm')
			if (!props.draggedSession.id) {
			  emit('createSession', {session: {...props.draggedSession, start: start.format(), end: end.format(), room: hoverSlice.value.room.id}})
			} else {
				emit('rescheduleSession', {session: props.draggedSession, start: start.format(), end: end.format(), room: hoverSlice.value.room})
			}
		}
		
		const expandTimeslice = (slice) => {
			const index = visibleTimeslices.value.indexOf(slice)
			if (index + 1 >= visibleTimeslices.value.length) {
				expandedTimes.value.push(slice.date.clone().add(5, 'm'))
			} else {
				const end = visibleTimeslices.value[index + 1].date.clone()
				let interval = 0
				if (end.diff(slice.date, 'minutes') <= 30) {
					interval = 5
				} else {
					interval = 30
				}
				const time = slice.date.clone().add(interval, 'm')
				while (time.isBefore(end)) {
					expandedTimes.value.push(time.clone())
					time.add(interval, 'm')
				}
			}
			expandedTimes.value = [...new Set(expandedTimes.value)]
		}
		
		const updateHoverSlice = (e) => {
			if (!props.draggedSession) { hoverSlice.value = null; return }
			if (!dragScrollTimer.value) {
				dragScrollTimer.value = setInterval(dragOnScroll, 100)
			}
			let hoverSliceElement = null
			for (const element of document.elementsFromPoint(gridOffset.value, e.clientY)) {
				if (element && element.dataset.slice && element.classList.contains('timeslice')) {
					hoverSliceElement = element
					break
				}
			}
			if (!hoverSliceElement) return
			const roomElements = document.querySelectorAll('.grid .room')
			if (roomElements.length < 2) return
			const roomWidth = roomElements[1].getBoundingClientRect().width
			const scrollOffset = scrollParent.value?.scrollLeft || 0
			const roomIndex = Math.floor((e.clientX + scrollOffset - gridOffset.value - 80) / roomWidth)
			if (roomIndex >= 0 && roomIndex < visibleRooms.value.length) {
				hoverSlice.value = { 
					time: moment(hoverSliceElement.dataset.slice), 
					roomIndex: roomIndex, 
					room: visibleRooms.value[roomIndex], 
					duration: props.draggedSession.duration 
				}
			}
		}
		
		const getHoverSliceStyle = () => {
			if (!hoverSlice.value || !props.draggedSession) return
			return { 
				'grid-area': `${getSliceName(hoverSlice.value.time)} / ${hoverSlice.value.roomIndex + 2} / ${getSliceName(hoverSlice.value.time.clone().add(hoverSlice.value.duration, 'm'))}`
			}
		}
		
		const getSessionStyle = (session) => {
			if (!session.room || !session.start) return {}
			const roomIndex = visibleRooms.value.indexOf(session.room)
			return {
				'grid-row': `${getSliceName(session.start)} / ${getSliceName(session.end)}`,
				'grid-column': roomIndex > -1 ? roomIndex + 2 : null
			}
		}
		
		const getOffsetTop = () => {
			return staticOffsetTop.value + window.scrollY
		}
		
		const getSliceClasses = (slice) => {
			return {
				datebreak: slice.datebreak,
				gap: slice.gap,
				expandable: isSliceExpandable(slice)
			}
		}
		
		const isSliceExpandable = (slice) => {
			const index = visibleTimeslices.value.indexOf(slice)
			if (index + 1 === visibleTimeslices.value.length) return false
			const nextSlice = visibleTimeslices.value[index + 1]
			return nextSlice.date.diff(slice.date, 'm') > 5
		}
		
		const getSliceStyle = (slice) => {
			if (slice.datebreak) {
				let index = timeslices.value.findIndex(s => s.date.isAfter(slice.date, 'day'))
				if (index < 0) index = timeslices.value.length - 1
				return {'grid-area': `${slice.name} / 1 / ${timeslices.value[index].name} / auto`}
			}
			return {'grid-area': `${slice.name} / 1 / auto / auto`}
		}
		
		const getSliceLabel = (slice) => {
			if (slice.datebreak) return slice.date.format('ddd[\n]DD. MMM')
			return slice.date.format('LT')
		}
		
		const changeDay = (day) => {
			if (scrolledDay.value && scrolledDay.value.isSame(day)) return
			const sliceName = getSliceName(day.startOf('day'))
			const el = sliceRefs.value[sliceName]
			if (el) {
				const offset = el.offsetTop + getOffsetTop()
				scrollTo(offset)
			}
		}
		
		const scrollTo = (offset) => {
			if (scrollParent.value) {
				scrollParent.value.scroll({top: offset, behavior: "smooth"})
			}
		}
		
		const scrollBy = (offset) => {
			if (scrollParent.value) {
				scrollParent.value.scrollBy({top: offset, behavior: "smooth"})
			}
		}
		
		const dragOnScroll = () => {
			if (!props.draggedSession) {
				clearInterval(dragScrollTimer.value)
				dragScrollTimer.value = null;
				return
			}
			const event = props.draggedSession.event
			if (!event) return
			
			const clientY = event.clientY
			const parentHeight = scrollParent.value?.clientHeight || 0
			
			if (clientY - staticOffsetTop.value < 160) {
				if (clientY - staticOffsetTop.value < 90) {
					scrollBy(-200)
				} else {
					scrollBy(-75)
				}
			} else if (clientY > parentHeight + staticOffsetTop.value - 100) {
				if (clientY > parentHeight + staticOffsetTop.value - 40) {
					scrollBy(200)
				} else {
					scrollBy(75)
				}
			}
		}
		
		const onIntersect = (entries) => {
			// Only observe datebreak slices (00:00 timeslices)
			const datebreakEntries = entries.filter(entry => 
				entry.target.classList.contains('datebreak')
			)
			if (!datebreakEntries.length) return
			
			// Find the most centered entry
			let mostCentered = null
			let minDistance = Infinity
			const viewportCenter = (scrollParent.value?.clientHeight || 0) / 2
			
			for (const entry of datebreakEntries) {
				if (entry.isIntersecting) {
					const rect = entry.target.getBoundingClientRect()
					const elementCenter = rect.top + rect.height / 2
					const distance = Math.abs(elementCenter - viewportCenter)
					
					if (distance < minDistance) {
						minDistance = distance
						mostCentered = entry
					}
				}
			}
			
			if (!mostCentered) return
			const day = moment.parseZone(mostCentered.target.dataset.slice).startOf('day')
			scrolledDay.value = day
			emit('changeDay', scrolledDay.value)
		}
		
		// Watchers
		watch(() => props.currentDay, changeDay)
		
		// Lifecycle hooks
		onMounted(async () => {
			await nextTick()
			if (gridRef.value) {
				gridOffset.value = gridRef.value.getBoundingClientRect().left
			}
			
			// Setup intersection observer only for datebreak slices
			observer.value = new IntersectionObserver(onIntersect, {
				root: scrollParent.value,
				rootMargin: '-45% 0px',
				threshold: 0.1
			})
		})
		
		onUnmounted(() => {
			if (observer.value) {
				observer.value.disconnect()
				observer.value = null
			}
			if (dragScrollTimer.value) {
				clearInterval(dragScrollTimer.value)
				dragScrollTimer.value = null
			}
		})
		
		return {
			// Refs
			rootRef,
			gridRef,
			scrolledDay,
			hoverSlice,
			expandedTimes,
			gridOffset,
			dragScrollTimer,
			dragStart,
			hiddenRooms,
			
			// Computed
			hoverSliceLegal,
			hoverEndSlice,
			timeslices,
			visibleTimeslices,
			oddTimeslices,
			gridStyle,
			gridClasses,
			availabilitySlices,
			staticOffsetTop,
			scrollParent,
			visibleRooms,
			visibleSessions,
			visibleAvailabilities,
			
			// Methods
			getLocalizedString,
			setSliceRef,
			startDragging,
			stopDragging,
			expandTimeslice,
			updateHoverSlice,
			getHoverSliceStyle,
			getSessionStyle,
			getOffsetTop,
			getSliceClasses,
			isSliceExpandable,
			getSliceStyle,
			getSliceLabel,
			changeDay,
			scrollTo,
			scrollBy,
			dragOnScroll
		}
	}
})
</script>
<style lang="stylus">
.c-grid-schedule
	flex: auto
	.grid
		background-color: $clr-grey-50
		display: grid
		grid-template-columns: 78px repeat(var(--total-rooms), 1fr) auto
		// grid-gap: 8px
		position: relative
		min-width: min-content
		&.illegal-hover
			cursor: not-allowed !important
			.c-linear-schedule-session
				cursor: not-allowed !important
		> .room
			position: sticky
			top: calc(48px)
			display: flex
			justify-content: center
			align-items: center
			font-size: 18px
			background-color: $clr-white
			border-bottom: border-separator()
			z-index: 20
			.hide-room
				color: $clr-secondary-text-light
				font-size: 14px
				margin-left: 16px
				cursor: pointer
				padding: 4px 8px
				border-radius: 4px
				&:hover
					background-color: $clr-grey-200
		.c-linear-schedule-session
			z-index: 10
	.timeslice
		color: $clr-secondary-text-light
		padding: 8px 10px 0 10px
		white-space: nowrap
		position: sticky
		left: 0
		text-align: center
		background-color: $clr-grey-50
		border-top: 1px solid $clr-dividers-light
		z-index: 20
		.expand
			display: none
		&.datebreak
			font-weight: 600
			border-top: 3px solid $clr-dividers-light
			white-space: pre
		&.expandable:hover
			background-color: $clr-grey-200
			cursor: pointer
			.expand
				display: block
				width: 20px
				margin: 4px auto
				path
					fill: $clr-grey-500

	.timeseparator
		height: 1px
		background-color: $clr-dividers-light
		position: absolute
		// transform: translate(-16px, -8px)
		width: 100%
		&.datebreak
			height: 3px
.bunt-scrollbar-rail-wrapper-x, .bunt-scrollbar-rail-wrapper-y
	z-index: 30
.availability
	background-color: white
	pointer-events: none
	&.active
		background-color: rgba(56, 158, 119, 0.1)
#hiddenRooms
	position: fixed
	z-index: 500
	bottom: 0
	right: 0
	width: 300px;
	background-color: $clr-white
	padding: 8px 16px
	box-shadow: 0 0 10px rgba(0, 0, 0, 0.3)
	border-top-left-radius: 8px
	font-size: 16px

	.room-list
		display: none

	&:hover
		.room-list
			display: block

	.room-entry
		border-bottom: border-separator()
		display: flex
		justify-content: space-between
		align-items: center
		height: 28px
		padding: 4px 0
		cursor: pointer
		.show-room
			color: $clr-secondary-text-light
			font-size: 14px
			margin-left: 16px
			padding: 4px 8px
			border-radius: 4px
		&:hover
			background-color: $clr-grey-100
</style>
