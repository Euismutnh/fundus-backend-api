def get_otp_email_template(otp: str, user_name: str = "User", purpose: str = "verification") -> str:
    """Get comprehensive HTML template for OTP email"""
    
    if purpose == "verification":
        title = "Verifikasi Akun"
        heading = "Verifikasi Akun Anda"
        message = "untuk menyelesaikan proses registrasi akun Anda"
        action_text = "verifikasi akun"
    elif purpose == "login":
        title = "Kode Login"
        heading = "Kode Verifikasi Login"
        message = "untuk melanjutkan proses login ke akun Anda"
        action_text = "login"
    else:  # reset
        title = "Reset Password"
        heading = "Reset Password Akun"
        message = "untuk mereset password akun Anda"
        action_text = "reset password"
    
    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - DR Detection App</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background-color: #f5f7fa;
                color: #333333;
            }}
            
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
                position: relative;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="50" r="0.5" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            }}
            
            .logo {{
                width: 80px;
                height: 80px;
                background: rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                position: relative;
                z-index: 1;
            }}
            
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
                position: relative;
                z-index: 1;
            }}
            
            .header p {{
                margin: 10px 0 0;
                font-size: 16px;
                opacity: 0.9;
                position: relative;
                z-index: 1;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 18px;
                margin-bottom: 20px;
                color: #4a5568;
            }}
            
            .message {{
                font-size: 16px;
                line-height: 1.8;
                margin-bottom: 30px;
                color: #2d3748;
            }}
            
            .otp-section {{
                text-align: center;
                margin: 40px 0;
            }}
            
            .otp-label {{
                font-size: 14px;
                color: #718096;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
            }}
            
            .otp-box {{
                background: linear-gradient(145deg, #f7fafc, #edf2f7);
                border: 3px dashed #667eea;
                border-radius: 16px;
                padding: 25px;
                margin: 20px auto;
                max-width: 300px;
                position: relative;
                overflow: hidden;
            }}
            
            .otp-box::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: linear-gradient(45deg, transparent, rgba(102, 126, 234, 0.1), transparent);
                transform: rotate(45deg);
                animation: shimmer 2s infinite;
            }}
            
            @keyframes shimmer {{
                0% {{ transform: translateX(-100%) translateY(-100%) rotate(45deg); }}
                100% {{ transform: translateX(100%) translateY(100%) rotate(45deg); }}
            }}
            
            .otp-code {{
                font-size: 36px;
                font-weight: 900;
                color: #667eea;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
                position: relative;
                z-index: 1;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .security-notice {{
                background: linear-gradient(135deg, #fed7d7, #feb2b2);
                border-left: 4px solid #e53e3e;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            
            .security-notice h3 {{
                color: #c53030;
                font-size: 16px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .security-notice ul {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            
            .security-notice li {{
                color: #742a2a;
                font-size: 14px;
                margin-bottom: 8px;
                padding-left: 20px;
                position: relative;
            }}
            
            .security-notice li::before {{
                content: '•';
                color: #e53e3e;
                position: absolute;
                left: 0;
                font-weight: bold;
            }}
            
            .help-section {{
                background: #f0fff4;
                border: 1px solid #9ae6b4;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
                text-align: center;
            }}
            
            .help-section h3 {{
                color: #276749;
                font-size: 16px;
                margin-bottom: 10px;
            }}
            
            .help-section p {{
                color: #2f855a;
                font-size: 14px;
                margin: 0;
            }}
            
            .footer {{
                background: linear-gradient(135deg, #2d3748, #4a5568);
                color: #e2e8f0;
                padding: 30px;
                text-align: center;
            }}
            
            .footer-content {{
                max-width: 400px;
                margin: 0 auto;
            }}
            
            .footer h3 {{
                color: #ffffff;
                font-size: 18px;
                margin-bottom: 15px;
            }}
            
            .footer p {{
                font-size: 14px;
                margin-bottom: 10px;
                opacity: 0.8;
            }}
            
            .social-links {{
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid rgba(226, 232, 240, 0.3);
            }}
            
            .social-links a {{
                color: #90cdf4;
                text-decoration: none;
                margin: 0 10px;
                font-size: 14px;
            }}
            
            .social-links a:hover {{
                color: #ffffff;
            }}
            
            .expiry-timer {{
                background: linear-gradient(135deg, #fff5b7, #fed7aa);
                border: 2px solid #f6ad55;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                text-align: center;
            }}
            
            .expiry-timer .timer-icon {{
                font-size: 20px;
                margin-right: 8px;
            }}
            
            .expiry-timer .timer-text {{
                color: #c05621;
                font-weight: 600;
                font-size: 14px;
            }}
            
            @media only screen and (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 8px;
                }}
                
                .header {{
                    padding: 30px 20px;
                }}
                
                .content {{
                    padding: 30px 20px;
                }}
                
                .otp-code {{
                    font-size: 28px;
                    letter-spacing: 6px;
                }}
                
                .footer {{
                    padding: 25px 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo">👁️</div>
                <h1>DR Detection App</h1>
                <p>{heading}</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Halo {user_name},
                </div>
                
                <div class="message">
                    Kami menerima permintaan {message}. Untuk melanjutkan proses {action_text}, silakan gunakan kode OTP berikut:
                </div>
                
                <div class="otp-section">
                    <div class="otp-label">Kode Verifikasi</div>
                    <div class="otp-box">
                        <div class="otp-code">{otp}</div>
                    </div>
                </div>
                
                <div class="expiry-timer">
                    <span class="timer-icon">⏰</span>
                    <span class="timer-text">Kode ini akan kedaluwarsa dalam 5 menit</span>
                </div>
                
                <div class="security-notice">
                    <h3>🔐 Penting untuk Keamanan Anda:</h3>
                    <ul>
                        <li>Kode OTP ini bersifat rahasia dan hanya untuk Anda</li>
                        <li>Jangan berikan kode ini kepada siapapun termasuk petugas kami</li>
                        <li>Kode akan kedaluwarsa otomatis setelah 5 menit</li>
                        <li>Jika Anda tidak meminta kode ini, segera hubungi tim support</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h3>🤝 Butuh Bantuan?</h3>
                    <p>Jika Anda mengalami kesulitan atau memiliki pertanyaan, jangan ragu untuk menghubungi tim support kami. Kami siap membantu Anda 24/7.</p>
                </div>
            </div>
            
            <div class="footer">
                <div class="footer-content">
                    <h3>DR Detection App</h3>
                    <p>Solusi AI untuk Deteksi Diabetic Retinopathy</p>
                    <p>&copy; 2025 DR Detection App. All rights reserved.</p>
                    <p><em>Email ini dikirim secara otomatis, mohon jangan balas email ini.</em></p>
                    
                    <div class="social-links">
                        <a href="#">Privacy Policy</a>
                        <a href="#">Terms of Service</a>
                        <a href="#">Support</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_email_template(user_name: str) -> str:
    """Welcome email template after successful registration"""
    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Selamat Datang - DR Detection App</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background-color: #f5f7fa;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .success-icon {{
                text-align: center;
                font-size: 64px;
                margin: 20px 0;
            }}
            .features {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            .feature-item {{
                display: flex;
                align-items: center;
                margin: 15px 0;
                padding: 10px;
                background: white;
                border-radius: 6px;
            }}
            .feature-icon {{
                font-size: 24px;
                margin-right: 15px;
                width: 40px;
                text-align: center;
            }}
            .footer {{
                background: #2d3748;
                color: #e2e8f0;
                padding: 30px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">👁️</div>
                <h1>DR Detection App</h1>
                <p>Selamat Datang di Platform Kami</p>
            </div>
            
            <div class="content">
                <div class="success-icon">🎉</div>
                
                <h2 style="text-align: center; color: #2d3748;">Selamat Datang, {user_name}!</h2>
                
                <p>Terima kasih telah bergabung dengan DR Detection App. Akun Anda telah berhasil diverifikasi dan siap digunakan.</p>
                
                <div class="features">
                    <h3 style="color: #2d3748; margin-bottom: 20px;">Fitur yang Tersedia:</h3>
                    
                    <div class="feature-item">
                        <div class="feature-icon">🔍</div>
                        <div>
                            <strong>Deteksi AI Akurat</strong><br>
                            <small>Teknologi AI terdepan untuk deteksi diabetic retinopathy</small>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <div class="feature-icon">📊</div>
                        <div>
                            <strong>Manajemen Pasien</strong><br>
                            <small>Kelola data pasien dengan mudah dan aman</small>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <div class="feature-icon">📱</div>
                        <div>
                            <strong>Akses Mobile</strong><br>
                            <small>Gunakan kapan saja, di mana saja melalui aplikasi mobile</small>
                        </div>
                    </div>
                    
                    <div class="feature-item">
                        <div class="feature-icon">🔒</div>
                        <div>
                            <strong>Keamanan Terjamin</strong><br>
                            <small>Data pasien dan hasil deteksi tersimpan dengan aman</small>
                        </div>
                    </div>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <strong>Mulai gunakan aplikasi sekarang dan rasakan kemudahan deteksi diabetic retinopathy dengan teknologi AI!</strong>
                </p>
            </div>
            
            <div class="footer">
                <h3>DR Detection App</h3>
                <p>Solusi AI untuk Deteksi Diabetic Retinopathy</p>
                <p>&copy; 2025 DR Detection App. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """