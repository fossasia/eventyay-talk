import { z } from 'zod';

const basePath = process.env.BASE_PATH || '/talk';

const SpeakerSchema = z.object({
  code: z.string(),
  name: z.string(),
});

// Title can be a string or a language object like {en: "Title"}
const toTitleRecord = (val: unknown): Record<string, string> => {
  if (val !== null && typeof val === 'object') {
    return val as Record<string, string>;
  }
  if (typeof val === 'string') {
    return { en: val };
  }
  return { en: '' };
};

// Room schema
const RoomSchema = z.object({
  id: z.number(),
  name: z.record(z.string(), z.string()).default({}),
  description: z.record(z.string(), z.string()).default({})
});

const TrackSchema = z.object({
  id: z.number(),
  name: z.record(z.string(), z.string()).default({})
});

// Talk schema
const TalkSchema = z.object({
  id: z.number(),
  // Some talks have code, some don't
  code: z.string().optional(),
  title: z.union([
    z.string(),
    z.record(z.string(), z.string())
  ]).transform(toTitleRecord),
  abstract: z.string().optional(),
  speakers: z.array(z.string()).optional().default([]),
  // Room and track come as numbers in the API
  room: z.union([
    z.number(),
    z.string().transform(val => parseInt(val, 10) || null)
  ]).nullable().optional(),
  track: z.union([
    z.number(),
    z.string().transform(val => parseInt(val, 10) || null)
  ]).nullable().optional(),

  start: z.string().nullable().optional(),
  end: z.string().nullable().optional(),
  state: z.string().optional(),
  updated: z.string().optional(),
  uncreated: z.boolean().optional(),
  availabilities: z.array(z.unknown()).optional().default([]),
  // Duration field - it appears some talks don't have this field
  duration: z.number().optional()
});

// Main schedule schema
const ScheduleSchema = z.object({
  version: z.nullable(z.string().nullable()),
  event_start: z.string(),
  event_end: z.string(),
  timezone: z.string(),
  locales: z.array(z.string()).default([]),
  rooms: z.array(RoomSchema).default([]),
  tracks: z.array(TrackSchema).default([]),
  speakers: z.array(SpeakerSchema).default([]),
  talks: z.array(TalkSchema).default([]),
  now: z.string().optional(),
  warnings: z.record(z.string(), z.any()).optional().default({})
});

const AvailabilitySchema = z.object({
  rooms: z.record(z.string(), z.array(z.object({ 
    start: z.string(), 
    end: z.string() 
  }))).optional(),
  talks: z.record(z.string(), z.array(z.object({ 
    start: z.string(), 
    end: z.string() 
  }))).optional(),
});

const WarningSchema = z.object({
  message: z.string(),
});

const WarningsSchema = z.record(z.string(), z.array(WarningSchema)).optional();
interface TalkPayload {
  id?: number;
  code?: string;
  title?: string | Record<string, string>;
  description?: string | Record<string, string>;
  room?: string | number | { id: string | number };
  start?: string;
  end?: string;
  duration?: number;
}

// Helper to calculate duration in minutes from start and end time strings
const calculateDuration = (start?: string, end?: string): number | undefined => {
  if (!start || !end) return undefined;
  
  try {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    return (endTime - startTime) / (1000 * 60); // Duration in minutes
  } catch (e) {
    return undefined;
  }
};

const api = {
  eventSlug: basePath ? window.location.pathname.split("/")[4] : window.location.pathname.split("/")[3],
  
  async http<T>(verb: string, url: string, body: unknown): Promise<T> {
    const headers: Record<string, string> = {};
    if (body) {
      headers['Content-Type'] = 'application/json';
    }

    const options: RequestInit = {
      method: verb || 'GET',
      headers,
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'include',
    };
    
    const response = await fetch(url, options);
    
    if (response.status === 204) {
      return undefined as unknown as T;
    }
    
    const json = await response.json();
    
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${JSON.stringify(json)}`);
    }
    
    return json as T;
  },

  async fetchTalks(options?: { since?: string; warnings?: boolean }): Promise<z.infer<typeof ScheduleSchema>> {
    let url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/talks/`;
    
    // Build query parameters
    const params = new URLSearchParams();
    if (window.location.search) {
      new URLSearchParams(window.location.search).forEach((value, key) => {
        params.append(key, value);
      });
    }
    if (options?.since) params.append('since', options.since);
    if (options?.warnings) params.append('warnings', 'true');
    
    url += `?${params.toString()}`;
    
    const data = await this.http('GET', url, null);
    return ScheduleSchema.parse(data);
  },

  async fetchAvailabilities(): Promise<z.infer<typeof AvailabilitySchema>> {
    const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/availabilities/`;
    const data = await this.http('GET', url, null);
    return AvailabilitySchema.parse(data);
  },

  async fetchWarnings(): Promise<z.infer<typeof WarningsSchema>> {
    const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/warnings/`;
    const data = await this.http('GET', url, null);
    return WarningsSchema.parse(data);
  },

  async saveTalk(
    talk: TalkPayload,
    { action = 'PATCH' }: { action?: string } = {}
  ): Promise<z.infer<typeof TalkSchema> | void> {
    const url = new URL(window.location.href);
    url.pathname = `${url.pathname}api/talks/${talk.id ? `${talk.id}/` : ''}`;
    url.search = window.location.search;

    let payload: unknown = undefined;
    if (action !== 'DELETE') {
      const roomId = talk.room && typeof talk.room === 'object' 
        ? talk.room.id 
        : talk.room;
        
      // Calculate duration if not provided but we have start and end times
      const duration = talk.duration ?? calculateDuration(talk.start, talk.end);
      
      payload = {
        room: roomId,
        start: talk.start,
        end: talk.end,
        duration: duration,
        title: talk.title,
        description: talk.description,
      };
    }
    
    // Make request
    const response = await this.http<unknown>(action, url.toString(), payload);
    
    // Validate and return response
    if (action !== 'DELETE') {
      return TalkSchema.parse(response);
    }
  },

  async deleteTalk(talk: { id: number }): Promise<void> {
    await this.saveTalk({ id: talk.id }, { action: 'DELETE' });
  },

  async createTalk(talk: Omit<TalkPayload, 'id'>): Promise<z.infer<typeof TalkSchema>> {
    const response = await this.saveTalk(talk, { action: 'POST' }) as z.infer<typeof TalkSchema>;
    return TalkSchema.parse(response);
  }
};

export default api
