import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { HlmBadgeImports } from '@shared/ui/badge';
import { HlmButtonImports } from '@shared/ui/button';
import { HlmCardImports } from '@shared/ui/card';
import { HlmInputImports } from '@shared/ui/input';
import { HlmLabelImports } from '@shared/ui/label';
import { SessionService } from '../../core/auth/session.service';
import { AUTH_CONFIG } from './AUTH_CONFIG';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    HlmBadgeImports,
    HlmButtonImports,
    HlmCardImports,
    HlmInputImports,
    HlmLabelImports,
  ],
  templateUrl: './login.page.html',
  styleUrl: './login.page.css',
})
export class LoginPage {
  private readonly fb = inject(FormBuilder);
  private readonly sessionService = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly config = AUTH_CONFIG;
  protected readonly enviando = signal(false);
  protected readonly errorMensaje = signal<string | null>(null);
  protected readonly esModoMock = this.sessionService.esModoMock;

  protected readonly form = this.fb.nonNullable.group({
    correo: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  protected get correoInvalido(): boolean {
    const control = this.form.controls.correo;
    return control.invalid && (control.dirty || control.touched);
  }

  protected get passwordInvalida(): boolean {
    const control = this.form.controls.password;
    return control.invalid && (control.dirty || control.touched);
  }

  protected onSubmit(): void {
    if (this.form.invalid || this.enviando()) {
      this.form.markAllAsTouched();
      return;
    }

    this.enviando.set(true);
    this.errorMensaje.set(null);

    const { correo, password } = this.form.getRawValue();

    this.sessionService.iniciarSesion(correo, password).subscribe({
      next: () => {
        this.enviando.set(false);
        this.router.navigate(['/inicio']);
      },
      error: (err: HttpErrorResponse) => {
        this.enviando.set(false);
        if (err.status === 400 || err.status === 401) {
          this.errorMensaje.set(this.config.errors.invalidCredentials);
        } else {
          this.errorMensaje.set(this.config.errors.serverError);
        }
      },
    });
  }
}