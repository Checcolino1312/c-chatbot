import { Component, ViewChild, ElementRef, AfterViewChecked, OnInit, HostListener, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatbotService } from './chatbot.service';
import { trigger, transition, style, animate } from '@angular/animations';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

interface Message {
  sender: string;
  text: string;
  timestamp: Date;
  isImage?: boolean;
  imageUrl?: SafeUrl;
}

@Component({
  selector: 'lib-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
  animations: [
    trigger('messageAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('chatAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ opacity: 0, transform: 'translateY(20px)' }))
      ])
    ])
  ]
})
export class ChatbotComponent implements OnInit, AfterViewChecked {
  @ViewChild('messageContainer') private messageContainer!: ElementRef;
  @ViewChild('messageInput') private messageInput!: ElementRef;

  @Input() position: 'bottom-right' | 'centered' = 'bottom-right';
  @Input() floatingButton: boolean = true;
  @Input() initialState: 'open' | 'closed' = 'closed';

  messages: Message[] = [];
  userMessage: string = '';
  isTyping: boolean = false;
  isOnline: boolean = true;
  isChatOpen: boolean = false;
  private lastInteractionTime: number = 0;

  constructor(
    private chatbotService: ChatbotService,
    private sanitizer: DomSanitizer
  ) { }

  ngOnInit() {
    this.isChatOpen = this.initialState === 'open';
    if (this.isChatOpen) {
      this.sendAutomaticHello();
    }
  }

  toggleChat() {
    this.isChatOpen = !this.isChatOpen;
    if (this.isChatOpen && this.messages.length === 0) {
      this.sendAutomaticHello();
    }
  }

  @HostListener('document:click')
  onDocumentClick() {
    this.lastInteractionTime = Date.now();
  }

  @HostListener('document:keydown')
  onDocumentKeydown() {
    this.lastInteractionTime = Date.now();
  }

  private isImageUrl(text: string): boolean {
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
    const urlPattern = /https?:\/\/[^\s]+/;

    if (!urlPattern.test(text)) return false;

    return imageExtensions.some(ext => text.toLowerCase().endsWith(ext));
  }

  private sanitizeUrl(url: string): SafeUrl {
    return this.sanitizer.bypassSecurityTrustUrl(url);
  }

  private handleBotResponse(msg: any): Message {
    if (msg.image) {
      const isImage = this.isImageUrl(msg.image);
      return {
        sender: 'bot',
        text: msg.text || msg.image,
        timestamp: new Date(),
        isImage: isImage,
        imageUrl: isImage ? this.sanitizeUrl(msg.image) : undefined
      };
    }

    return {
      sender: 'bot',
      text: msg.text,
      timestamp: new Date(),
      isImage: false
    };
  }

  private focusInput() {
    if (Date.now() - this.lastInteractionTime > 300) {
      setTimeout(() => {
        this.messageInput?.nativeElement?.focus();
      }, 100);
    }
  }

  private sendAutomaticHello() {
    this.isTyping = true;

    setTimeout(() => {
      this.chatbotService
        .sendMessage('utente1', 'ciao')
        .subscribe({
          next: (response) => {
            response.forEach((msg: any) => {
              this.messages.push(this.handleBotResponse(msg));
            });
            this.isOnline = true;
            this.isTyping = false;
            this.focusInput();
          },
          error: (_) => {
            this.messages.push({
              sender: 'bot',
              text: 'Mi dispiace, si è verificato un errore.',
              timestamp: new Date()
            });
            this.isOnline = false;
            this.isTyping = false;
            this.focusInput();
          }
        });
    }, 1000);
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    try {
      this.messageContainer.nativeElement.scrollTop =
        this.messageContainer.nativeElement.scrollHeight;
    } catch (err) { }
  }

  onImageError(imageUrl: string): void {
    console.log('Error loading image:', imageUrl);
  }

  onImageLoad(imageUrl: string): void {
    console.log('Image loaded successfully:', imageUrl);
  }

  sendMessage(): void {
    if (this.userMessage.trim()) {
      this.messages.push({
        sender: 'user',
        text: this.userMessage,
        timestamp: new Date()
      });

      const userMsg = this.userMessage;
      this.userMessage = '';
      this.isTyping = true;

      setTimeout(() => {
        this.chatbotService
          .sendMessage('utente1', userMsg)
          .subscribe({
            next: (response) => {
              response.forEach((msg: any) => {
                this.messages.push(this.handleBotResponse(msg));
              });
              this.isOnline = true;
              this.isTyping = false;
              this.focusInput();
            },
            error: (_) => {
              this.messages.push({
                sender: 'bot',
                text: 'Mi dispiace, si è verificato un errore.',
                timestamp: new Date()
              });
              this.isOnline = false;
              this.isTyping = false;
              this.focusInput();
            }
          });
      }, 500);
    }
  }
}