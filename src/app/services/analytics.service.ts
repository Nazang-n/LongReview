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
}
