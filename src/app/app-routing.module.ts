// app-routing.module.ts
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Import Component เข้ามาเพื่อนำไปใช้ใน routes
import { HomeComponent } from './home/home.component';
import { NewsComponent } from './home/news/news.component';
import { FavoritesComponent } from './home/favorites/favorites.component';
import { GameListComponent } from './home/game-list/game-list.component';
import { GameDetailComponent } from './home/game-detail/game-detail.component';
import { ProfileComponent } from './home/profile/profile.component';
import { LoginComponent } from './auth/login.component';
import { RegisterComponent } from './auth/register.component';
import { NewsDetailComponent } from './home/news-detail/news-detail.component';

import { AuthGuard } from './guards/auth.guard';
import { AdminGuard } from './guards/admin.guard';
import { AdminComponent } from './admin/admin.component';

const routes: Routes = [
  // หน้าแรก (Home)
  { path: '', component: HomeComponent },

  { path: 'news', component: NewsComponent },
  { path: 'news/:id', component: NewsDetailComponent },
  { path: 'favorites', component: FavoritesComponent, canActivate: [AuthGuard] },
  { path: 'games', component: GameListComponent },
  { path: 'game/:id', component: GameDetailComponent },
  { path: 'profile', component: ProfileComponent, canActivate: [AuthGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'admin', component: AdminComponent, canActivate: [AdminGuard] },

  // (Optional) กรณีพิมพ์ URL ผิดให้กลับไปหน้าแรก
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes)
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }