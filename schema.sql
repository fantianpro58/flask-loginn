-- Jalankan di Supabase: menu SQL Editor -> New query -> paste -> Run

create table if not exists users (
  id            serial primary key,
  username      varchar(50)  unique not null,
  password_hash varchar(255) not null,
  nama          varchar(100),
  created_at    timestamptz  default now()
);

-- User demo -> username: admin | password: admin123
-- (password sudah di-hash; ganti/hapus setelah testing)
insert into users (username, password_hash, nama)
values (
  'admin',
  'scrypt:32768:8:1$nimpqzuuSnxRDX6F$a382fa2bed5a9f45c0679b8970099afd09bdfafe06356332e620b115289fa4cb07d076f960087acec34a25e762ed15ea6c9f7a0b4a8ba58dbaf77c006a83bc4e',
  'Administrator'
)
on conflict (username) do nothing;
