# A4: Auth – Login & Protect

Secure authentication and route protection system built with FastAPI and Supabase Auth (IdP).

## Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/public/info` | Public status message | No |
| `POST` | `/auth/signup` | Register a new user | No |
| `POST` | `/auth/login` | Authenticate and obtain JWT | No |
| `POST` | `/auth/logout` | Terminate session | Yes (`Bearer <token>`) |
| `GET` | `/protected/profile` | Read authenticated user metadata | Yes (`Bearer <token>`) |
| `GET` | `/protected/dashboard` | Read private dashboard analytics | Yes (`Bearer <token>`) |

## Setup & Running

1. Copy `.env.example` to `.env` and configure your Supabase URL & Anon Key:
   ```env
   SUPABASE_URL=[https://your-project.supabase.co](https://your-project.supabase.co)
   SUPABASE_KEY=your-anon-key