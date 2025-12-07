import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomepageComponent } from './homepage/homepage.component';
import { NewspageComponent } from './newspage/newspage.component';
import { GamepageComponent } from './gamepage/gamepage.component';

const routes: Routes = [
  { path: '', component: HomepageComponent },
  { path: 'home', component: HomepageComponent },
  { path: 'news', component: NewspageComponent },
  { path: 'game', component: GamepageComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class WebpageRoutingModule { }
