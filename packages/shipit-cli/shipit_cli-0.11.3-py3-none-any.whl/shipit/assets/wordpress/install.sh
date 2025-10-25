# Needed to get the WP-CLI commands to avoid asking for the TTY size
IFS=$'\n\t'

export COLUMNS=80  # Prevent WP-CLI from asking for TTY size
export PAGER="cat"

wp() {
  php /opt/assets/wp-cli.phar --allow-root --path=/app "$@"
}

echo "🚀 Starting WordPress setup..."

echo "Creating required directories..."

mkdir -p wp-content/plugins
mkdir -p wp-content/upgrade

echo "Installing WordPress core"

wp core install \
  --url="$WP_SITEURL"  \
  --title="$WP_SITE_TITLE" \
  --admin_user="$WP_ADMIN_USERNAME" \
  --admin_password="$WP_ADMIN_PASSWORD" \
  --admin_email="$WP_ADMIN_EMAIL" \
  --locale="$WP_LOCALE"


if [ "${WP_UPDATE_DB:-false}" = "true" ]; then
    echo "Updating database..."
    wp core update-db
fi

# Install plugins from WP_PLUGINS environment variable
if [ -n "${WP_PLUGINS:-}" ]; then
  echo "Installing plugins from WP_PLUGINS: $WP_PLUGINS"

  IFS=','  # Split by commas
  for PLUGIN_ENTRY in $WP_PLUGINS; do
    if [[ "$PLUGIN_ENTRY" =~ ^https?:// ]]; then
      echo "Installing plugin from URL: $PLUGIN_ENTRY"
      wp plugin install "$PLUGIN_ENTRY" --activate
    else
      # Extract name and version using parameter expansion
      PLUGIN_NAME="${PLUGIN_ENTRY%%:*}"
      PLUGIN_VERSION="${PLUGIN_ENTRY#*:}"

      if [[ "$PLUGIN_NAME" == "$PLUGIN_VERSION" ]]; then
        echo "Installing plugin '${PLUGIN_NAME}' (latest version)..."
        wp plugin install "$PLUGIN_NAME" --activate
      else
        echo "Installing plugin '${PLUGIN_NAME}' (version: ${PLUGIN_VERSION})..."
        wp plugin install "$PLUGIN_NAME" --version="$PLUGIN_VERSION" --activate
      fi
    fi
  done
fi

# Install themes from WP_THEMES environment variable
if [ -n "${WP_THEMES:-}" ]; then
  echo "🎨 Installing themes from WP_THEMES: $WP_THEMES"
  IFS=','

  for THEME_ENTRY in $WP_THEMES; do
    if [[ "$THEME_ENTRY" =~ ^https?:// ]]; then
      echo "Installing theme from URL: $THEME_ENTRY"
      wp theme install "$THEME_ENTRY"
    else
      THEME_NAME="${THEME_ENTRY%%:*}"
      THEME_VERSION="${THEME_ENTRY#*:}"

      if [[ "$THEME_NAME" == "$THEME_VERSION" ]]; then
        echo "Installing theme '${THEME_NAME}' (latest version)..."
        wp theme install "$THEME_NAME"
      else
        echo "Installing theme '${THEME_NAME}' (version: ${THEME_VERSION})..."
        wp theme install "$THEME_NAME" --version="$THEME_VERSION"
      fi
    fi
  done
fi

if [ -n "${WP_DEFAULT_THEME:-}" ]; then
  echo "Activating default theme: $WP_DEFAULT_THEME"
  wp theme activate "$WP_DEFAULT_THEME"
fi

echo "✅ WordPress Installation complete"
