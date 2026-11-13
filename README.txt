САЙТ NFS OWN MUSIC — https://kotovskivan.github.io/NFSOwnMusic/
Общий сайт серии: все NFS на PC, у каждой статус — Готово / Скоро / «?» Чекає.
Репо: https://github.com/kotovskivan/NFSOwnMusic  — main = эта папка (исходник), gh-pages = готовый сайт (папка gotovo).
Хостинг: GitHub Pages (бесплатно). Собран 13.11.2026, дизайн черновой (Ваня: «прикинь, потом сделаем дизайн»).
Страницы: / — украинский (главный), /en/ /de/ /es/ /fr/ /it/ /pl/ /pt/ /tr/ /ru/ /zh/ /ja/ /ko/ /fi/ (fi — 13.11 вечер). Переводы — ИИ (Claude).

КАК ОБНОВИТЬ
  1. Игра поменяла статус (вышла программа, взялись за новую часть) -> igry.txt: ready / soon / wait
     + программа: ключ (unbound, heat, …) 4-м полем, а в sajt.txt строки <ключ>_name / _version / _site / _download / _code.
     Новая программа = новые строки в sajt.txt, тексты кнопок уже есть во всех языках.
  2. Версия Unbound / Heat поменялась -> sajt.txt: unbound_version / heat_version (+ heat_download, когда Heat выйдет).
  3. Тексты -> teksty\<язык>.txt (ключи одинаковые во всех 14; нет ключа — возьмется из en.txt, сборка напишет).
  4. prosmotr.cmd    — собрать и посмотреть в браузере (http://localhost:8766/)
     opublikovat.cmd — собрать и отправить на GitHub (исходник -> main, сайт -> gh-pages), сайт обновится через 1-2 минуты.

ЧТО ГДЕ
  shablon.html  разметка и стиль, один на все языки (менять — Claude). Цвета статусов — в начале <style>.
  sobrat.py     сборщик: shablon + teksty + sajt.txt + igry.txt -> gotovo\
  static\       иконка (favicon.svg), .nojekyll — копируются как есть
                googleeef38fee5f2ab13e.html — подтверждение Google Search Console файлом (13.11 вечер), НЕ удалять — слетит доступ
  gotovo\       готовый сайт = ветка gh-pages (git worktree), руками не править — пересоберется

SEO — СДЕЛАНО
  title / description на каждом языке под поиск («своя музыка / custom music / eigene Musik…» + Need for Speed),
  canonical + hreflang (14 языков + x-default = en), Open Graph / Twitter, JSON-LD (WebSite + программы, что вышли),
  sitemap.xml, полные названия всех игр текстом на странице, подсказка «есть на твоем языке» вместо автоперехода.
  Нет пока: картинки превью ссылки (og:image) — сделаем вместе с дизайном.

SEO — СДЕЛАТЬ ТЕБЕ (один раз, как у Unbound)
  1. (13.11 вечер: Ваня подтверждает ФАЙЛОМ — он уже в static и в сети; тег google_verify не нужен)
     Google Search Console -> Добавить ресурс -> «Префикс URL»: https://kotovskivan.github.io/NFSOwnMusic/
     -> «HTML-тег» -> content="..." -> sajt.txt (google_verify = ...) -> opublikovat.cmd -> «Подтвердить».
     Потом: Файлы Sitemap -> sitemap.xml -> Отправить.
  2. Bing Webmaster Tools — «Импорт из Google Search Console».
  3. Ссылки на этот сайт: README репо Unbound и Heat, сайт Unbound, Steam-гайд, Nexus.
