const basePath = process.env.BASE_PATH || '/talk';

interface ApiResponse<T> {
    results?: T[];
    next?: string;
    [key: string]: unknown;
}

interface Talk {
    id?: string;
    code?: string;
    title?: string | Record<string, string>;
    description?: string | Record<string, string>;
    room?: string | { id: string };
    start?: string;
    end?: string;
    duration?: number;
}

const api = {
    eventSlug: basePath ? window.location.pathname.split("/")[4] : window.location.pathname.split("/")[3],
    
    http<T>(verb: string, url: string, body: unknown): Promise<T | void> {
        const options = {
            method: verb || 'GET',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined,
            credentials: 'include' as const,
        }
        return window.fetch(url, options)
            .then(response => {
                if (response.status === 204) return Promise.resolve();
                return response.json().then(json => {
                    if (!response.ok) return Promise.reject({ response, json });
                    return Promise.resolve(json as T);
                });
            });
    },

    getList<T>(url: string): Promise<T[]> {
        return this.http<ApiResponse<T>>('GET', url, null).then((response) => {
            if (!response) return [];
            
            if (response.next) {
                return this.getList<T>(response.next).then(nextPage => {
                    return [...(response.results || []), ...nextPage];
                });
            }
            return response.results || [];
        });
    },

    fetchTalks(options?: { since?: string; warnings?: boolean }): Promise<ApiResponse<Talk>> {
        let url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/talks/`;
        if (window.location.search) {
            url += window.location.search + '&';
        } else {
            url += '?';
        }
        if (options?.since) {
            url += `since=${encodeURIComponent(options.since)}&`;
        }
        if (options?.warnings) {
            url += 'warnings=true';
        }
        
        // Cast to the expected type since this endpoint always returns JSON
        return this.http('GET', url, null) as Promise<ApiResponse<Talk>>;
    },

    fetchAvailabilities(): Promise<unknown> {
        const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/availabilities/`;
        return this.http('GET', url, null);
    },

    fetchWarnings(): Promise<unknown> {
        const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/warnings/`;
        return this.http('GET', url, null);
    },

    saveTalk(talk: Talk, { action = 'PATCH' }: { action?: string } = {}): Promise<Talk | void> {
        const url = [
            window.location.protocol,
            '//',
            window.location.host,
            window.location.pathname,
            'api/talks/',
            talk.id ? `${talk.id}/` : '',
            window.location.search,
        ].join('');
        
        const payload = {
            room: (talk.room && typeof talk.room === 'object') ? talk.room.id : talk.room,
            start: talk.start,
            end: talk.end,
            duration: talk.duration,
            title: talk.title,
            description: talk.description,
        };
        
        return this.http<Talk>(action, url, payload);
    },

    deleteTalk(talk: { id: string }): Promise<void> {
        return this.saveTalk({ id: talk.id }, { action: 'DELETE' }) as Promise<void>;
    },

    createTalk(talk: Talk): Promise<Talk | void> {
        return this.saveTalk(talk, { action: 'POST' });
    }
}

export default api
