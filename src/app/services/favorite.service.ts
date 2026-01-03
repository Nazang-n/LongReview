import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface FavoriteResponse {
    success: boolean;
    message: string;
    is_favorited: boolean;
}

@Injectable({
    providedIn: 'root'
})
export class FavoriteService {
    private apiUrl = 'http://localhost:8000/api/favorites';

    constructor(private http: HttpClient) { }

    /**
     * Add a game to user's favorites
     */
    addFavorite(userId: number, gameId: number): Observable<FavoriteResponse> {
        return this.http.post<FavoriteResponse>(`${this.apiUrl}/${gameId}`, { user_id: userId });
    }

    /**
     * Remove a game from user's favorites
     */
    removeFavorite(userId: number, gameId: number): Observable<FavoriteResponse> {
        return this.http.delete<FavoriteResponse>(`${this.apiUrl}/${gameId}`, {
            body: { user_id: userId }
        });
    }

    /**
     * Get all favorite games for a user
     */
    getUserFavorites(userId: number): Observable<any[]> {
        const params = new HttpParams().set('user_id', userId.toString());
        return this.http.get<any[]>(this.apiUrl, { params });
    }

    /**
     * Check if a game is in user's favorites
     */
    isFavorited(userId: number, gameId: number): Observable<FavoriteResponse> {
        const params = new HttpParams().set('user_id', userId.toString());
        return this.http.get<FavoriteResponse>(`${this.apiUrl}/check/${gameId}`, { params });
    }
}
