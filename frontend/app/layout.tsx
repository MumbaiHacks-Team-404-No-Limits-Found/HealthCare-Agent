import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import { AuthProvider } from '@/context/AuthContext';
import ApolloProviderWrapper from '@/components/providers/ApolloProviderWrapper';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Healthcare Volunteer Coordinator',
  description: 'Manage medical camp volunteers and assignments',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <ApolloProviderWrapper>
            {children}
          </ApolloProviderWrapper>
        </AuthProvider>
      </body>
    </html>
  );
}

