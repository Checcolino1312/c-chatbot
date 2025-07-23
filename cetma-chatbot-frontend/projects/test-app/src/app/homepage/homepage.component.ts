import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { ChatbotComponent } from '../../../../chatbot/src/lib/chatbot.component';

@Component({
  selector: 'app-homepage',
  standalone: true,
  imports: [CommonModule, ChatbotComponent, RouterModule],
  templateUrl: './homepage.component.html',
  styleUrls: ['./homepage.component.scss']
})
export class HomepageComponent { }