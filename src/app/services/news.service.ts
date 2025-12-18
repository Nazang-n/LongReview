import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

// Internal NewsItem interface
export interface NewsItem {
    id: string;
    title: string;
    description?: string;
    image: string;
    link: string;
    date?: string;
    author?: string;
}

export interface NewsResponse {
    status: string;
    news: NewsItem[];
    nextPage?: string;
    totalResults: number;
    skip?: number;
    limit?: number;
    hasMore?: boolean;
}

@Injectable({
    providedIn: 'root'
})
export class NewsService {
    private readonly API_URL = 'http://localhost:8000/news';

    // Simple cache to avoid excessive API calls
    private cache: Map<string, NewsResponse> = new Map();

    constructor(private http: HttpClient) { }

    /**
     * Fetch news from backend API
     * @param nextPage Optional pagination token (deprecated, use skip instead)
     * @param skip Number of articles to skip for pagination
     * @param limit Number of articles to return
     * @returns Observable of NewsResponse
     */
    getNews(nextPage?: string | null, skip: number = 0, limit: number = 30): Observable<NewsResponse> {
        const cacheKey = `skip-${skip}-limit-${limit}`;

        // Check cache first
        if (this.cache.has(cacheKey)) {
            return of(this.cache.get(cacheKey)!);
        }

        // Build URL with parameters
        let url = `${this.API_URL}?skip=${skip}&limit=${limit}`;

        return this.http.get<NewsResponse>(url).pipe(
            map(response => {
                // Cache the response
                this.cache.set(cacheKey, response);
                return response;
            }),
            catchError(this.handleError)
        );
    }

    /**
     * Get featured news (first article from latest news)
     */
    getFeaturedNews(): Observable<NewsItem | null> {
        return this.http.get<NewsItem>(`${this.API_URL}/featured`).pipe(
            catchError(() => of(null))
        );
    }

    /**
     * Get latest news for home page
     * @param limit Number of articles to return
     */
    getLatestNews(limit: number = 5): Observable<NewsItem[]> {
        return this.getNews().pipe(
            map(response => response.news.slice(0, limit)),
            catchError(() => of([]))
        );
    }

    /**
     * Manually trigger news sync from API (admin only)
     */
    syncNews(): Observable<any> {
        return this.http.post(`${this.API_URL}/sync`, {}).pipe(
            map(response => {
                // Clear cache after sync to show fresh data
                this.clearCache();
                return response;
            }),
            catchError(this.handleError)
        );
    }

    /**
     * Handle HTTP errors
     */
    private handleError(error: HttpErrorResponse) {
        let errorMessage = 'เกิดข้อผิดพลาดในการโหลดข่าว';

        if (error.error instanceof ErrorEvent) {
            // Client-side error
            errorMessage = `ข้อผิดพลาด: ${error.error.message}`;
        } else {
            // Server-side error
            errorMessage = error.error?.detail || `เซิร์ฟเวอร์ตอบกลับด้วยรหัส ${error.status}`;
        }

        console.error('NewsService Error:', errorMessage, error);
        return throwError(() => new Error(errorMessage));
    }

    /**
     * Clear cache (useful for refresh)
     */
    clearCache(): void {
        this.cache.clear();
    }
}
