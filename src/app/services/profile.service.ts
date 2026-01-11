import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserProfile {
    id: number;
    username: string;
    email: string;
    user_role: string;
    avatar_url: string | null;
    created_at: string;
}

export interface UserStats {
    total_comments: number;
    favorites: number;
}

export interface UserComment {
    id: number;
    game_id: number;
    game_title: string;
    game_image: string | null;
    content: string;
    is_edited: boolean;
    created_at: string;
    updated_at: string;
    upvotes: number;
}

@Injectable({
    providedIn: 'root'
})
export class ProfileService {
    private apiUrl = 'http://localhost:8000/api/profile';

    constructor(private http: HttpClient) { }

    /**
     * Get user profile
     */
    getProfile(userId: number): Observable<UserProfile> {
        return this.http.get<UserProfile>(`${this.apiUrl}/${userId}`);
    }

    /**
     * Update user profile
     */
    updateProfile(userId: number, username: string, email: string): Observable<any> {
        return this.http.put(`${this.apiUrl}/${userId}`, {
            username,
            email
        });
    }

    /**
     * Update avatar
     */
    updateAvatar(userId: number, avatarUrl: string): Observable<any> {
        return this.http.post(`${this.apiUrl}/${userId}/avatar`, {
            avatar_url: avatarUrl
        });
    }

    /**
     * Change password
     */
    changePassword(userId: number, currentPassword: string, newPassword: string): Observable<any> {
        return this.http.put(`${this.apiUrl}/${userId}/password`, {
            current_password: currentPassword,
            new_password: newPassword
        });
    }

    /**
     * Get user comments
     */
    getUserComments(userId: number): Observable<UserComment[]> {
        return this.http.get<UserComment[]>(`${this.apiUrl}/${userId}/comments`);
    }

    /**
     * Get user statistics
     */
    getUserStats(userId: number): Observable<UserStats> {
        return this.http.get<UserStats>(`${this.apiUrl}/${userId}/stats`);
    }

    /**
     * Delete avatar
     */
    deleteAvatar(userId: number): Observable<any> {
        return this.http.delete(`${this.apiUrl}/${userId}/avatar`);
    }
}
