---
layout: default
title: About FastOpp
permalink: /about/
---

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="prose prose-lg max-w-none">
        <h1 class="text-4xl font-bold text-gray-900 mb-8">About FastOpp</h1>
        
        <div class="bg-gradient-to-r from-ai-blue to-ai-purple text-white p-8 rounded-xl mb-12">
            <h2 class="text-2xl font-bold mb-4">What is FastOpp?</h2>
            <p class="text-lg">
                FastOpp is a FastAPI starter package designed for students prototyping AI web applications. 
                It provides pre-built admin components that give FastAPI functionality comparable to Django 
                for AI-first applications.
            </p>
        </div>
        
        <h2 class="text-3xl font-bold text-gray-900 mb-6">The Problem We Solve</h2>
        <p class="text-lg text-gray-700 mb-6">
            Django and Flask are not designed for optimized async LLM applications. While both can absolutely 
            be used for complex AI applications and are great in many ways, there are often rough patches 
            during development of asynchronous AI applications that communicate with backend LLMs available 
            at OpenAI, Anthropic, and OpenRouter.
        </p>
        
        <p class="text-lg text-gray-700 mb-8">
            FastAPI has advantages in future-proof architecture, but can have a steep learning curve for 
            people, especially for developers familiar with Django. FastOpp bridges this gap by providing 
            an opinionated framework for FastAPI with Django-inspired features.
        </p>
        
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Key Features</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">Admin Panel</h3>
                <p class="text-gray-600">
                    Django-style admin panel with role-based authentication, similar to Django admin 
                    but built for FastAPI.
                </p>
            </div>
            
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">SQL Database</h3>
                <p class="text-gray-600">
                    SQL database with Django-inspired models and migrations using SQLModel and Alembic.
                </p>
            </div>
            
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">Modern UI</h3>
                <p class="text-gray-600">
                    Tailwind CSS, DaisyUI, Alpine.js, and HTMX for beautiful, interactive interfaces.
                </p>
            </div>
            
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">API Endpoints</h3>
                <p class="text-gray-600">
                    Auto-generated API documentation and endpoints designed to connect with React and Flutter.
                </p>
            </div>
        </div>
        
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Target Audience</h2>
        <p class="text-lg text-gray-700 mb-6">
            FastOpp is opinionated and may not be for everyone. It is intended for students and novice 
            developers who know Python, but are not strong in or do not like JavaScript.
        </p>
        
        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-8">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-yellow-700">
                        <strong>Important:</strong> FastOpp is not intended for production use or for experienced developers.
                    </p>
                </div>
            </div>
        </div>
        
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Example Use Cases</h2>
        <div class="space-y-6 mb-12">
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-3">University Students</h3>
                <p class="text-gray-600">
                    Looking to build resume projects to show potential employers that you can build an AI application. 
                    You want to host it cheaply and use cheap or free LLMs with the option to use a higher-quality 
                    LLM before you show off your project.
                </p>
            </div>
            
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-3">Hobbyists</h3>
                <p class="text-gray-600">
                    Looking to vibe code simple AI utilities. Provide Cursor or equivalent access to demos and 
                    start with an opinionated structure for files and UI. Enforce vibe-code behavior with rules 
                    so that you can go back and edit your code.
                </p>
            </div>
            
            <div class="bg-white rounded-xl shadow-lg p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-3">Small Business Entrepreneurs</h3>
                <p class="text-gray-600">
                    You have great business ideas, but you are not a great programmer. You want to put AI into 
                    a business workflow that you are familiar with and show other people to get more help.
                </p>
            </div>
        </div>
        
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Get Started</h2>
        <p class="text-lg text-gray-700 mb-8">
            Ready to start building with FastOpp? Check out our quick start guide and create your own 
            repository from our template.
        </p>
        
        <div class="flex flex-col sm:flex-row gap-4">
            <a href="https://github.com/Oppkey/FastOpp" 
               class="inline-flex items-center justify-center border-2 border-ai-blue text-ai-blue bg-white px-8 py-3 rounded-lg font-semibold hover:bg-ai-blue hover:text-white transition-colors"
               target="_blank" rel="noopener">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                View on GitHub
            </a>
            
            <a href="https://github.com/Oppkey/FastOpp#-quick-start-for-students" 
               class="inline-flex items-center justify-center border-2 border-ai-blue text-ai-blue px-8 py-3 rounded-lg font-semibold hover:bg-ai-blue hover:text-white transition-colors"
               target="_blank" rel="noopener">
                Quick Start Guide
            </a>
        </div>
    </div>
</div>
