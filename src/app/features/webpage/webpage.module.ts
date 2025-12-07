import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HomepageComponent } from './homepage/homepage.component';
import { NewspageComponent } from './newspage/newspage.component';
import { GamepageComponent } from './gamepage/gamepage.component';
import { WebpageRoutingModule } from './webpage.routing.module';

import { providePrimeNG } from 'primeng/config';

import aura from '@primeng/themes/aura';


import { CheckboxModule } from 'primeng/checkbox';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TableModule } from 'primeng/table';
import { ConfirmationService, MessageService } from 'primeng/api';
import { TagModule } from 'primeng/tag';
import { DynamicDialogModule } from 'primeng/dynamicdialog';
import { ToastModule } from 'primeng/toast';


@NgModule({
  declarations: [
    HomepageComponent,
    NewspageComponent,
    GamepageComponent
  ],
  imports: [
    CommonModule,
    WebpageRoutingModule,
    CheckboxModule,
    ConfirmDialogModule,
    TableModule,
    TagModule,
    DynamicDialogModule,
    ToastModule
  ],
  providers: [
    providePrimeNG({
      theme: {
        preset: aura,
        options: {
          darkModeSelector: '[data-theme=dark]'
        }
      },
    }),

    ConfirmationService,
    MessageService
  ],
})
export class WebpageModule {

}
