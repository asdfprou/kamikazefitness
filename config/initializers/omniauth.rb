OmniAuth.config.logger = Rails.logger

Rails.application.config.middleware.use OmniAuth::Builder do
  provider :facebook, '541365185935224', '7fc10157712fe6fce4afa8e48925aa62'
end
