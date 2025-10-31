/**
 * Добро пожаловать в панель управления UtodevBotnet
 * @author: utodevbotnet
 */

import Head from 'next/head'
import Botnet from './components/botnet'

export default function Home() {
    return (
        <div>
            <Head>
                <title>UtodevBotnet v3 - Панель управления ботами</title>
                <meta name="description" content="Панель управления для стресс-тестирования сайтов" />
                <link rel="icon" href="/favicon.ico" />
            </Head>
            <header>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src="/Hulk.png"
                    alt="UtodevBotnet"
                    width={100}
                    height={100}
                />
                <h1 style={{
                    textAlign: 'center',
                    fontSize: '3em'
                }}>
                    UtodevBotnet v3 - Панель управления ботами
                </h1>
            </header>
            <main>
                <Botnet />
            </main>
        </div>
    )
}
