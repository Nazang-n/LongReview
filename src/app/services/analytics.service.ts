import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DailyStatistic {
    date: string;
    count: number;
}

export interface AnalyticsResponse {
    daily: DailyStatistic[];
    monthly_total: number;
    today_count: number;
}

export interface NewGamesTodayResponse {
    date: string;
    new_games_count: number;
    logs: {
        time: string | null;
        count: number;
        status: string;
    }[];
}

export interface DailyUpdateStatus {
    fetched: boolean;
    status: string;
    count: number;
    time: string | null;
}

export interface DailyUpdatesResponse {
    date: string;
    updates: {
        news: DailyUpdateStatus;
        games: DailyUpdateStatus;
        sentiment: DailyUpdateStatus;
        tags: DailyUpdateStatus;
        reviews: DailyUpdateStatus;
    };
}

export interface IncompleteGame {
    id: number;
    title: string;
    steam_app_id: number;
    not_updated: string[];
    last_sentiment_update: string | null;
    last_tags_update: string | null;
    last_review_fetch: string | null;
}

export interface IncompleteGamesResponse {
    total_not_updated: number;
    games: IncompleteGame[];
}

@Injectable({
    providedIn: 'root'
})
export class AnalyticsService {
    private apiUrl = 'http://localhost:8000/api/admin/analytics';

    constructor(private http: HttpClient) { }

    getCommentAnalytics(): Observable<AnalyticsResponse> {
        return this.http.get<AnalyticsResponse>(`${this.apiUrl}/comments`);
    }

    getNewsAnalytics(): Observable<AnalyticsResponse> {
        return this.http.get<AnalyticsResponse>(`${this.apiUrl}/news`);
    }

    getReportAnalytics(): Observable<AnalyticsResponse> {
        return this.http.get<AnalyticsResponse>(`${this.apiUrl}/reports`);
    }

    getNewGamesToday(): Observable<NewGamesTodayResponse> {
        return this.http.get<NewGamesTodayResponse>(`${this.apiUrl}/new-games-today`);
    }

    getDailyUpdates(): Observable<DailyUpdatesResponse> {
        return this.http.get<DailyUpdatesResponse>(`${this.apiUrl}/daily-updates`);
    }

    getIncompleteGames(): Observable<IncompleteGamesResponse> {
        return this.http.get<IncompleteGamesResponse>(`${this.apiUrl}/incomplete-games`);
    }
}
