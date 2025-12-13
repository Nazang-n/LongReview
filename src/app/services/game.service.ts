import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
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

@Injectable({
    providedIn: 'root'
})
export class GameService {
    private apiUrl = 'http://localhost:8000/api/games';

    constructor(private http: HttpClient) { }

    /**
     * Get all games with optional pagination
     */
    getGames(skip: number = 0, limit: number = 100): Observable<Game[]> {
        const params = new HttpParams()
            .set('skip', skip.toString())
            .set('limit', limit.toString());
        return this.http.get<Game[]>(this.apiUrl, { params });
    }

    /**
     * Get a specific game by ID
     */
    getGame(id: number): Observable<Game> {
        return this.http.get<Game>(`${this.apiUrl}/${id}`);
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
}
