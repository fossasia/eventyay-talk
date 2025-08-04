import { 
  ScheduleSchema, 
  AvailabilitySchema, 
  WarningsSchema, 
  TalkSchema,
  Talk,
  Schedule,
  Availability,
  Warnings
} from './schemas';

const basePath = process.env.BASE_PATH || '/talk';

const calculateDuration = (start?: string, end?: string): number | undefined => {
  if (!start || !end) return undefined;
  try {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    return (endTime - startTime) / (1000 * 60);
  } catch {
    return undefined;
  }
};

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

const api = {
  eventSlug: basePath ? window.location.pathname.split("/")[4] : window.location.pathname.split("/")[3],
  
  async http<T>(verb: string, url: string, body: unknown): Promise<T> {
    const headers: Record<string, string> = {};
    if (body) headers['Content-Type'] = 'application/json';

    const options: RequestInit = {
      method: verb,
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

  async fetchTalks(options?: { since?: string; warnings?: boolean }): Promise<Schedule> {
    let url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/talks/`;
    const params = new URLSearchParams(window.location.search);
    if (options?.since) params.append('since', options.since);
    if (options?.warnings) params.append('warnings', 'true');
    url += `?${params.toString()}`;
    
    const data = await this.http<unknown>('GET', url, null);
    return ScheduleSchema.parse(data);
  },

  async fetchAvailabilities(): Promise<Availability> {
    const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/availabilities/`;
    const data = await this.http<unknown>('GET', url, null);
    return AvailabilitySchema.parse(data);
  },

  async fetchWarnings(): Promise<Warnings> {
    const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/warnings/`;
    const data = await this.http<unknown>('GET', url, null);
    return WarningsSchema.parse(data);
  },

  async saveTalk(
    talk: TalkPayload,
    { action = 'PATCH' }: { action?: string } = {}
  ): Promise<Talk | void> {
    const url = new URL(window.location.href);
    url.pathname = `${url.pathname}api/talks/${talk.id ? `${talk.id}/` : ''}`;
    url.search = window.location.search;

    let payload: unknown = undefined;
    if (action !== 'DELETE') {
      const roomId = typeof talk.room === 'object' ? talk.room.id : talk.room;
      const duration = talk.duration ?? calculateDuration(talk.start, talk.end);
      
      payload = {
        room: roomId,
        start: talk.start,
        end: talk.end,
        duration,
        title: talk.title,
        description: talk.description,
      };
    }
    
    const response = await this.http<unknown>(action, url.toString(), payload);
    
    if (action !== 'DELETE') {
      return TalkSchema.parse(response);
    }
  },

  async deleteTalk(talk: { id: number }): Promise<void> {
    await this.saveTalk({ id: talk.id }, { action: 'DELETE' });
  },

  async createTalk(talk: Omit<TalkPayload, 'id'>): Promise<Talk> {
    const response = await this.saveTalk(talk, { action: 'POST' });
    if (!response) {
      throw new Error('Failed to create talk: No response from server');
    }
    return response;
  }
};

export default api