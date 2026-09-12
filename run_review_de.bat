@echo off
@rem SPDX-FileCopyrightText: 2026 Peter Bezemek
@rem SPDX-License-Identifier: Apache-2.0 OR MIT
call "%~dp0run_review.bat" --language de --db "%~dp0tests\data\foreign_review\de.sqlite" --decisions "%~dp0tests\data\foreign_review\de_decisions.sqlite" %*
