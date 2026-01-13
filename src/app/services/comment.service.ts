import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Comment {
    id: number;
    game_id: number;
    user_id: number;
    username: string;
    content: string;
    is_edited: boolean;
    created_at: string;
    updated_at: string;
    upvotes: number;
    downvotes: number;
    user_vote: string | null;
    user_voted?: boolean;
}

export interface CommentReport {
    id: number;
    comment_id: number;
    comment_content: string;
    comment_user_id: number;
    game_id: number;
    game_title: string;
    reporter_id: number;
    reporter_username: string;
    reason: string;
    status: string;
    created_at: string;
}

@Injectable({
    providedIn: 'root'
})
export class CommentService {
    private apiUrl = 'http://localhost:8000/api/comments';

    constructor(private http: HttpClient) { }

    /**
     * Get all comments for a game
     */
    getComments(gameId: number, userId?: number): Observable<Comment[]> {
        let params = new HttpParams();
        if (userId) {
            params = params.set('user_id', userId.toString());
        }
        return this.http.get<Comment[]>(`${this.apiUrl}/${gameId}`, { params });
    }

    /**
     * Add a new comment
     */
    addComment(gameId: number, userId: number, content: string): Observable<any> {
        return this.http.post(`${this.apiUrl}/${gameId}`, {
            user_id: userId,
            content: content
        });
    }

    /**
     * Edit a comment
     */
    editComment(commentId: number, userId: number, content: string): Observable<any> {
        return this.http.put(`${this.apiUrl}/${commentId}`, {
            user_id: userId,
            content: content
        });
    }

    /**
     * Delete a comment
     */
    deleteComment(commentId: number, userId: number): Observable<any> {
        const params = new HttpParams().set('user_id', userId.toString());
        return this.http.delete(`${this.apiUrl}/${commentId}`, { params });
    }

    /**
     * Like a comment
     */
    likeComment(commentId: number, userId: number): Observable<any> {
        return this.http.post(`${this.apiUrl}/${commentId}/like`, {
            user_id: userId
        });
    }

    /**
     * Report a comment
     */
    reportComment(commentId: number, userId: number, reason: string): Observable<any> {
        return this.http.post(`${this.apiUrl}/${commentId}/report`, {
            user_id: userId,
            reason: reason
        });
    }

    /**
     * Get all reported comments (admin only)
     */
    getAllReports(userId: number): Observable<CommentReport[]> {
        const params = new HttpParams().set('user_id', userId.toString());
        return this.http.get<CommentReport[]>(`${this.apiUrl}/reports/all`, { params });
    }

    /**
     * Dismiss a report (admin only)
     */
    dismissReport(reportId: number, userId: number): Observable<any> {
        const params = new HttpParams().set('user_id', userId.toString());
        return this.http.put(`${this.apiUrl}/reports/${reportId}/dismiss`, {}, { params });
    }
}
