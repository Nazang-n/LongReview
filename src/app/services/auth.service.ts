import { Injectable, PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface User {
    id: number;
    username: string;
    email: string;
    user_role: string;
    is_active: boolean;
    created_at: string;
    updated_at?: string;
}

export interface RegisterRequest {
    username: string;
    email: string;
    password: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private apiUrl = 'https://longreview.onrender.com/api/auth';
    private currentUser: BehaviorSubject<User | null>;

    constructor(
        private http: HttpClient,
        @Inject(PLATFORM_ID) private platformId: Object
    ) {
        this.currentUser = new BehaviorSubject<User | null>(this.getUserFromStorage());
    }

    /**
     * Register a new user
     */
    register(data: RegisterRequest): Observable<User> {
        return this.http.post<User>(`${this.apiUrl}/register`, data).pipe(
            tap(user => {
                this.setCurrentUser(user);
            })
        );
    }

    /**
     * Login with email and password
     */
    login(data: LoginRequest): Observable<User> {
        return this.http.post<User>(`${this.apiUrl}/login`, data).pipe(
            tap(user => {
                this.setCurrentUser(user);
            })
        );
    }

    /**
     * Get current user observable
     */
    getCurrentUser(): Observable<User | null> {
        return this.currentUser.asObservable();
    }

    /**
     * Get current user value synchronously
     */
    getCurrentUserValue(): User | null {
        return this.currentUser.value;
    }

    /**
     * Check if user is logged in
     */
    isLoggedIn(): boolean {
        return this.currentUser.value !== null;
    }

    /**
     * Check if current user is admin
     */
    isAdmin(): boolean {
        const user = this.currentUser.value;
        return user !== null && user.user_role === 'Admin';
    }

    /**
     * Logout user
     */
    logout(): void {
        if (isPlatformBrowser(this.platformId)) {
            localStorage.removeItem('currentUser');
        }
        this.currentUser.next(null);
    }

    /**
     * Set current user and store in localStorage
     */
    private setCurrentUser(user: User): void {
        if (isPlatformBrowser(this.platformId)) {
            localStorage.setItem('currentUser', JSON.stringify(user));
        }
        this.currentUser.next(user);
    }

    /**
     * Get user from localStorage
     */
    private getUserFromStorage(): User | null {
        if (isPlatformBrowser(this.platformId)) {
            const user = localStorage.getItem('currentUser');
            return user ? JSON.parse(user) : null;
        }
        return null;
    }

    /**
     * Get user by ID
     */
    getUser(userId: number): Observable<User> {
        return this.http.get<User>(`${this.apiUrl}/user/${userId}`);
    }
}
