import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Review {
    id?: number;
    game_id: number;
    user_id: number;
    title?: string;
    content: string;
    rating: number;
    created_at?: string;
    updated_at?: string;
}

@Injectable({
    providedIn: 'root'
})
export class ReviewService {
    private apiUrl = 'https://longreview.onrender.com/api/reviews';

    constructor(private http: HttpClient) { }

    /**
     * Get all reviews with optional pagination
     */
    getReviews(skip: number = 0, limit: number = 100): Observable<Review[]> {
        const params = new HttpParams()
            .set('skip', skip.toString())
            .set('limit', limit.toString());
        return this.http.get<Review[]>(this.apiUrl, { params });
    }

    /**
     * Get reviews for a specific game
     */
    getReviewsByGame(gameId: number, skip: number = 0, limit: number = 100): Observable<Review[]> {
        const params = new HttpParams()
            .set('skip', skip.toString())
            .set('limit', limit.toString());
        return this.http.get<Review[]>(`${this.apiUrl}/game/${gameId}`, { params });
    }

    /**
     * Get a specific review by ID
     */
    getReview(id: number): Observable<Review> {
        return this.http.get<Review>(`${this.apiUrl}/${id}`);
    }

    /**
     * Create a new review
     */
    createReview(review: Review): Observable<Review> {
        return this.http.post<Review>(this.apiUrl, review);
    }

    /**
     * Update an existing review
     */
    updateReview(id: number, review: Partial<Review>): Observable<Review> {
        return this.http.put<Review>(`${this.apiUrl}/${id}`, review);
    }

    /**
     * Delete a review
     */
    deleteReview(id: number): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/${id}`);
    }
}
