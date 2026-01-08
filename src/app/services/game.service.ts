import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
// import { environment } from '../../environments/environment';

export interface Game {
    id?: number;
    title: string;
    description?: string;
    genre?: string;
    rating?: number;
    image_url?: string;
    release_date?: string;
    developer?: string;
    publisher?: string;
    created_at?: string;
    updated_at?: string;
}

export interface SteamSpyGame {
    appid: string;
    name: string;
    developer: string;
    publisher: string;
    owners: string;
    genre: string;
    positive?: number;
    negative?: number;
}

export interface SteamGameDetails {
    steam_appid: number;
    name: string;
    short_description: string;
    header_image: string;
    release_date: {
        date: string;
    };
    developers: string[];
    publishers: string[];
    genres: Array<{ description: string }>;
}

@Injectable({
    providedIn: 'root'
})
export class GameService {
    private apiUrl = 'http://localhost:8000/api/games';
    private steamApiUrl = 'http://localhost:8000/api/steam';

    constructor(private http: HttpClient) { }

    /**
     * Get all games with optional pagination and tag filtering
     */
    getGames(skip: number = 0, limit: number = 100, tagIds?: number[], sortBy: string = 'newest'): Observable<Game[]> {
        let params = new HttpParams()
            .set('skip', skip.toString())
            .set('limit', limit.toString())
            .set('sort_by', sortBy);

        // Add tag filtering if provided
        if (tagIds && tagIds.length > 0) {
            params = params.set('tags', tagIds.join(','));
        }

        return this.http.get<Game[]>(this.apiUrl, { params });
    }

    /**
     * Get a specific game by ID
     */
    getGame(id: number): Observable<Game> {
        return this.http.get<Game>(`${this.apiUrl}/${id}`);
    }

    /**
     * Get total count of games, optionally filtered by tags
     */
    getGamesCount(tagIds?: number[]): Observable<{ total: number }> {
        let params = new HttpParams();

        if (tagIds && tagIds.length > 0) {
            params = params.set('tags', tagIds.join(','));
        }

        return this.http.get<{ total: number }>(`${this.apiUrl}/count`, { params });
    }

    /**
     * Create a new game
     */
    createGame(game: Game): Observable<Game> {
        return this.http.post<Game>(this.apiUrl, game);
    }

    /**
     * Update an existing game
     */
    updateGame(id: number, game: Partial<Game>): Observable<Game> {
        return this.http.put<Game>(`${this.apiUrl}/${id}`, game);
    }

    /**
     * Delete a game
     */
    deleteGame(id: number): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/${id}`);
    }

    /**
     * Search games by query
     */
    searchGames(query: string, skip: number = 0, limit: number = 100): Observable<Game[]> {
        const params = new HttpParams()
            .set('query', query)
            .set('skip', skip.toString())
            .set('limit', limit.toString());
        return this.http.get<Game[]>(`${this.apiUrl}/search/`, { params });
    }

    /**
     * Get top games from SteamSpy
     */
    getTopGamesFromSteamSpy(limit: number = 50): Observable<any> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<any>(`${this.steamApiUrl}/steamspy/top`, { params });
    }

    /**
     * Get all games from SteamSpy
     */
    getAllGamesFromSteamSpy(limit?: number): Observable<any> {
        let params = new HttpParams();
        if (limit) {
            params = params.set('limit', limit.toString());
        }
        return this.http.get<any>(`${this.steamApiUrl}/steamspy/all`, { params });
    }

    /**
     * Get game details from Steam API
     */
    getSteamGameDetails(appId: number): Observable<any> {
        return this.http.get<any>(`${this.steamApiUrl}/app/${appId}`);
    }

    /**
     * Get game details from SteamSpy
     */
    getSteamSpyGameDetails(appId: number): Observable<any> {
        return this.http.get<any>(`${this.steamApiUrl}/steamspy/game/${appId}`);
    }

    /**
     * Import games from SteamSpy to database
     */
    importGamesFromSteamSpy(limit: number = 50): Observable<any> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.post<any>(`${this.steamApiUrl}/steamspy/import/batch`, null, { params });
    }

    /**
     * Sync Steam reviews for a game (fetch from Steam if not in database)
     */
    syncSteamReviews(gameId: number, maxReviews: number = 20): Observable<any> {
        const params = new HttpParams().set('max_reviews', maxReviews.toString());
        return this.http.post<any>(`http://localhost:8000/api/reviews/sync-steam/${gameId}`, null, { params });
    }

    /**
     * Get sentiment analysis from Steam reviews
     */
    getSteamSentiment(gameId: number): Observable<any> {
        return this.http.get<any>(`http://localhost:8000/api/reviews/sentiment/${gameId}`);
    }

    /**
     * Get sentiment for multiple games at once (for game list)
     */
    getBatchSentiment(gameIds: number[]): Observable<any> {
        return this.http.post<any>('http://localhost:8000/api/reviews/sentiment/batch', gameIds);
    }

    /**
     * Get review tags (positive/negative keywords from Thai reviews)
     */
    getReviewTags(gameId: number, refresh: boolean = false): Observable<any> {
        const params = new HttpParams().set('refresh', refresh.toString());
        return this.http.get<any>(`${this.apiUrl}/${gameId}/review-tags`, { params });
    }
    /**
     * Batch translate games that don't have Thai descriptions
     */
    batchTranslateGames(limit: number = 10000): Observable<any> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.post<any>('http://localhost:8000/api/games/translate/batch', null, { params });
    }

    /**
     * Manually trigger review update scheduler
     */
    triggerReviewUpdate(): Observable<any> {
        return this.http.post<any>(`${this.steamApiUrl}/admin/trigger-review-update`, {});
    }

    /**
     * Manually trigger sentiment cache update
     */
    triggerSentimentUpdate(): Observable<any> {
        return this.http.post<any>('http://localhost:8000/api/reviews/sentiment/update-all', {});
    }

    /**
     * Manually trigger review tags update for all games
     */
    triggerReviewTagsUpdate(): Observable<any> {
        return this.http.post<any>('http://localhost:8000/api/admin/review-tags/update', {});
    }
}
