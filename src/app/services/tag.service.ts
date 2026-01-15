import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Tag {
    id: number;
    name: string;
    name_th: string;
    type: string;
}

export interface TagWithCount extends Tag {
    game_count: number;
}

export interface TagStats {
    success: boolean;
    stats: {
        genres: TagWithCount[];
        platforms: TagWithCount[];
        player_modes: TagWithCount[];
    };
}

@Injectable({
    providedIn: 'root'
})
export class TagService {
    private apiUrl = 'http://localhost:8000/api/tags';

    constructor(private http: HttpClient) { }

    /**
     * Get all tags with statistics (game counts)
     */
    getTagStats(): Observable<TagStats> {
        return this.http.get<TagStats>(`${this.apiUrl}/stats`);
    }

    /**
     * Get tags by type
     */
    getTagsByType(type: 'genre' | 'platform' | 'player_mode'): Observable<{ success: boolean; tags: Tag[] }> {
        return this.http.get<{ success: boolean; tags: Tag[] }>(`${this.apiUrl}?type=${type}`);
    }

    /**
     * Migrate existing data to tags (run once)
     */
    migrateTags(): Observable<any> {
        return this.http.post(`${this.apiUrl}/migrate`, {});
    }
}
