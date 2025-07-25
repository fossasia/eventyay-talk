const basePath = process.env.BASE_PATH || '/talk';

interface ApiResponse {
    results?: any[];
    next?: string;
    [key: string]: any;
}

interface Talk {
    id?: string;
    code?: string;
    title?: any;
    description?: string;
    room?: string | { id: string };
    start?: string;
    end?: string;
    duration?: number;
}

const api = {
    eventSlug: basePath ? window.location.pathname.split("/")[4] : window.location.pathname.split("/")[3],
    
    http(verb: string, url: string, body: any): Promise<any> {
        const options = {
            method: verb || 'GET',
            headers: { 'Content-Type': 'application/json' },
            body: body && JSON.stringify(body),
            credentials: 'include' as const,
        }
        return window.fetch(url, options)
            .then(response => {
                if (response.status === 204) return Promise.resolve()
                return response.json().then(json => {
                    if (!response.ok) return Promise.reject({ response, json })
                    return Promise.resolve(json)
                })
            })
    },

    getList(url: string): Promise<any[]> {
        return this.http('GET', url, null).then((response: ApiResponse) => {
            if (response.next) {
                return this.getList(response.next).then(nextPage => {
                    return response.results!.concat(nextPage)
                })
            }
            return response.results!
        })
    },

    fetchTalks(options?: { since?: string; warnings?: boolean }): Promise<any> {
        let url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/talks/`
        if (window.location.search) {
            url += window.location.search + '&'
        } else {
            url += '?'
        }
        if (options?.since) {
            url += `since=${encodeURIComponent(options.since)}&`
        }
        if (options?.warnings) {
            url += 'warnings=true'
        }
        return this.http('GET', url, null)
    },

    fetchAvailabilities(): Promise<any> {
        const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/availabilities/`
        return this.http('GET', url, null)
    },

    fetchWarnings(): Promise<any> {
        const url = `${basePath}/orga/event/${this.eventSlug}/schedule/api/warnings/`
        return this.http('GET', url, null)
    },

    saveTalk(talk: Talk, { action = 'PATCH' }: { action?: string } = {}): Promise<any> {
        const url = [
            window.location.protocol,
            '//',
            window.location.host,
            window.location.pathname,
            'api/talks/',
            talk.id ? `${talk.id}/` : '',
            window.location.search,
        ].join('')
        return this.http(action, url, {
            room: (talk.room && typeof talk.room === 'object') ? talk.room.id : talk.room,
            start: talk.start,
            end: talk.end,
            duration: talk.duration,
            title: talk.title,
            description: talk.description,
        })
    },

    deleteTalk(talk: { id: string }): Promise<any> {
        return this.saveTalk({ id: talk.id }, { action: 'DELETE' })
    },

    createTalk(talk: Talk): Promise<any> {
        return this.saveTalk(talk, { action: 'POST' })
    }
}

export default api
