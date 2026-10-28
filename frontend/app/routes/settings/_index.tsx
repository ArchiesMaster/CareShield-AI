const SettingsPage = () => {
  return (
    <div className='flex flex-col h-[calc(100vh-56px)] bg-gray-100'>
      <div className='max-w-3xl mx-auto w-full px-6 py-10'>
        <h1 className='text-3xl font-bold text-purple-700 mb-4'>Settings</h1>

        <div className='bg-white rounded-xl shadow p-6'>
          <p className='text-gray-700'>Settings are not implemented in the current prototype.</p>

          <p className='text-gray-500 mt-3'>
            This section is reserved for future development, such as user preferences, account settings, notification
            options, and system configuration.
          </p>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
