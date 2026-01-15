import { Injectable, PLATFORM_ID, Inject } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { AuthService } from '../services/auth.service';

@Injectable({ providedIn: 'root' })
export class AdminGuard implements CanActivate {
    constructor(
        private router: Router,
        private authService: AuthService,
        @Inject(PLATFORM_ID) private platformId: Object
    ) { }

    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
        if (!isPlatformBrowser(this.platformId)) {
            return true;
        }

        // Check if user is logged in and is admin
        if (this.authService.isLoggedIn() && this.authService.isAdmin()) {
            return true;
        }

        // Not admin, redirect to home
        this.router.navigate(['/']);
        return false;
    }
}
